# Guia de Implantação de Produção: Atlas ERP no Google Cloud

Este guia segue as práticas recomendadas de **DevSecOps e Engenharia de Confiabilidade (SRE)** para homologação e publicação do Atlas ERP no **Google Cloud Platform (GCP)**.

> **IMPORTANTE — Onde executar este script:**
> Execute estes comandos no **[Google Cloud Shell](https://shell.cloud.google.com/)** (terminal Linux gratuito no próprio navegador do GCP).
> **Evite rodar comandos bash/echo no PowerShell do Windows**, pois utilitários como `echo -n` gravam parâmetros literais nas credenciais e corrompem as senhas no Secret Manager.

---

## 1. Arquitetura da Solução

```
[ Acesso Seguro ]
        │
        ├──► Pré-Produção/Homologação: gcloud run services proxy (ou IAP)
        │
        ▼
[ Google Cloud Run (Container Seguro) ]
  • Service Account dedicada: atlaserp-sa (não usa a conta padrão)
  • Acesso não-público inicial: --no-allow-unauthenticated
  • Concorrência alinhada: --concurrency 8 --max-instances 5 --memory 1Gi
  • Container: Python 3.12 + Gunicorn (2 workers x 4 threads) executando como appuser (não-root)
        │
        ├──► [ Secret Manager ] (Permissão restrita aos 4 segredos da aplicação)
        │
        ▼ (Unix Socket via Cloud SQL Auth Proxy nativo)
[ Google Cloud SQL (MySQL 8.4 LTS) ]
  • Versão: MySQL 8.4 LTS (Enterprise Edition)
  • Usuário exclusivo: atlaserp_user (sem privilégios de root)
  • Pool SQLAlchemy: pool_size=5, max_overflow=2 por worker
  • Backups automáticos diários com Point-in-Time Recovery (bin-log)
```

---

## 2. Preparação do Projeto e APIs no Cloud Shell

No Cloud Shell, defina as variáveis de ambiente:

```bash
export PROJECT_ID="SEU_PROJETO_ID"
export REGION="southamerica-east1"

gcloud config set project $PROJECT_ID

# Ativação das APIs essenciais
gcloud services enable \
    run.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com
```

---

## 3. Criação da Conta de Serviço Dedicada (Menor Privilégio)

Nunca utilize a conta padrão de computação com papéis amplos. Crie uma identidade exclusiva:

```bash
# 1. Cria a Service Account
gcloud iam service-accounts create atlaserp-sa \
    --display-name="Service Account do Atlas ERP"

export SA_EMAIL="atlaserp-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# 2. Concede permissão para conectar ao Cloud SQL
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/cloudsql.client"
```

---

## 4. Banco de Dados Cloud SQL (MySQL 8.4 LTS)

### A. Criar a instância
```bash
# Instância MySQL 8.4 Enterprise Edition
gcloud sql instances create atlaserp-db \
    --database-version=MYSQL_8_4 \
    --edition=ENTERPRISE \
    --tier=db-custom-1-3840 \
    --region=$REGION \
    --backup-start-time=03:00 \
    --enable-bin-log \
    --deletion-protection
```
*(Nota: Para testes e homologação com custo reduzido, é possível alterar o tier para `db-n1-standard-1` ou `db-g1-small`).*

### B. Criar a base e o usuário com senha aleatória
```bash
# 1. Cria a base de dados
gcloud sql databases create atlas_erp --instance=atlaserp-db

# 2. Gera uma senha forte hexadecimal (sem caracteres especiais que quebram parsing de URL)
export DB_PASS=$(openssl rand -hex 16)

# 3. Cria o usuário exclusivo
gcloud sql users create atlaserp_user \
    --instance=atlaserp-db \
    --password="$DB_PASS"

# 4. Imutabilidade no Banco de Dados: Garante que o usuario da aplicacao
# NUNCA tenha permissao de UPDATE ou DELETE na tabela de auditoria:
# GRANT SELECT, INSERT, UPDATE, DELETE ON atlas_erp.* TO 'atlaserp_user'@'%';
# REVOKE UPDATE, DELETE ON atlas_erp.audit_logs FROM 'atlaserp_user'@'%';
```

---

## 5. Armazenamento Seguro no Secret Manager

Criamos os segredos e liberamos acesso **estritamente para a Service Account `atlaserp-sa`**:

```bash
# 1. Conexão com o banco
printf "mysql+pymysql://atlaserp_user:%s@/atlas_erp?unix_socket=/cloudsql/%s:%s:atlaserp-db" "$DB_PASS" "$PROJECT_ID" "$REGION" | \
    gcloud secrets create atlaserp_database_url --data-file=-

# 2. Chave de criptografia de sessão Flask
openssl rand -hex 32 | tr -d '\n' | \
    gcloud secrets create atlaserp_secret_key --data-file=-

# 3. Senha administrativa inicial
openssl rand -hex 12 | tr -d '\n' | \
    gcloud secrets create atlaserp_admin_password --data-file=-

# 4. Senha do módulo financeiro
openssl rand -hex 12 | tr -d '\n' | \
    gcloud secrets create atlaserp_financial_password --data-file=-

# 5. Concede leitura dos segredos exclusivamente à Service Account
for SECRET in atlaserp_database_url atlaserp_secret_key atlaserp_admin_password atlaserp_financial_password; do
    gcloud secrets add-iam-policy-binding $SECRET \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="roles/secretmanager.secretAccessor"
done
```

---

## 6. Deploy no Google Cloud Run (Modo Seguro / Não-Público)

Para garantir segurança enquanto o sistema não possui autenticação individual por usuário (RBAC), implantamos com `--no-allow-unauthenticated`:

```bash
gcloud run deploy atlas-erp \
    --source . \
    --region=$REGION \
    --platform=managed \
    --no-allow-unauthenticated \
    --service-account="${SA_EMAIL}" \
    --memory=1Gi \
    --concurrency=8 \
    --max-instances=5 \
    --min-instances=0 \
    --add-cloudsql-instances="${PROJECT_ID}:${REGION}:atlaserp-db" \
    --set-env-vars="FLASK_ENV=production,ERP_EMERGENCY_ADMIN_ENABLED=false" \
    --set-secrets="DATABASE_URL=atlaserp_database_url:latest,SECRET_KEY=atlaserp_secret_key:latest"
```

### Como acessar o ERP para testes e homologação segura:
Como o acesso público direto está bloqueado, você e sua equipe acessam o sistema via túnel autenticado do Google:
```bash
gcloud run services proxy atlas-erp --region=$REGION
```
O comando abrirá um endereço local (`http://127.0.0.1:8080`) que redireciona de forma criptografada para o Cloud Run autenticado pela sua conta Google.

---

## 7. Execução de Migrações (Cloud Run Jobs)

O Job recebe a Service Account dedicada e todas as credenciais necessárias:

```bash
# 1. Cria o Job
gcloud run jobs create atlaserp-migrate \
    --image=$(gcloud run services describe atlas-erp --region=$REGION --format='value(spec.template.spec.containers[0].image)') \
    --region=$REGION \
    --service-account="${SA_EMAIL}" \
    --set-cloudsql-instances="${PROJECT_ID}:${REGION}:atlaserp-db" \
    --set-secrets="DATABASE_URL=atlaserp_database_url:latest,SECRET_KEY=atlaserp_secret_key:latest,ERP_ADMIN_PASSWORD=atlaserp_admin_password:latest,FINANCIAL_ACCESS_PASSWORD=atlaserp_financial_password:latest" \
    --command=python \
    --args="-m,flask,--app,run.py,db,upgrade"

# 2. Executa a migração das tabelas
gcloud run jobs execute atlaserp-migrate --region=$REGION --wait

# 3. Seed inicial do RBAC (Criação de perfis, permissões e usuário administrador inicial)
gcloud run jobs create atlaserp-seed-auth \
    --image=$(gcloud run services describe atlas-erp --region=$REGION --format='value(spec.template.spec.containers[0].image)') \
    --region=$REGION \
    --service-account="${SA_EMAIL}" \
    --set-cloudsql-instances="${PROJECT_ID}:${REGION}:atlaserp-db" \
    --set-secrets="DATABASE_URL=atlaserp_database_url:latest,SECRET_KEY=atlaserp_secret_key:latest" \
    --command=python \
    --args="-c,from app import create_app; from app.seed_auth import seed_rbac; app=create_app(); app.app_context().push(); seed_rbac()"

gcloud run jobs execute atlaserp-seed-auth --region=$REGION --wait
```

---

## 8. Checklist de Homologação (Staging Gate) e Pré-Produção

Antes de autorizar o tráfego de produção com dados empresariais reais, execute os seguintes passos de validação:

1. **Validação Direta no Cloud SQL MySQL 8.4 LTS:**
   - Execute a suíte de testes conectando via Cloud SQL Auth Proxy:
     ```bash
     $env:TEST_DATABASE_URL="mysql+pymysql://atlaserp_user:SENHA@127.0.0.1:3306/atlas_erp"
     pytest
     ```
   - Confirme a aprovação de todos os 162 testes contra o banco gerenciado na nuvem.

2. **Homologação em Ambiente Fechado (Zero Public Exposure):**
   - Mantenha o serviço provisionado com `--no-allow-unauthenticated`.
   - Realize os testes de homologação pelo túnel:
     ```bash
     gcloud run services proxy atlas-erp --region=$REGION
     ```

3. **Teste de Recuperação de Desastres (PITR & Backup):**
   - Na console do Cloud SQL, valide a retenção dos logs binários (`--enable-bin-log`).
   - Simule a criação de uma réplica/clone a partir de um ponto no tempo (PITR) para atestar o RPO (Recovery Point Objective).

4. **Diretriz para Uploads e Anexos (Google Cloud Storage - GCS):**
   - O filesystem dos containers no Cloud Run é **efêmero**. Qualquer arquivo salvo em disco local é descartado quando a instância encerra ou escala.
   - Para envio de anexos, recibos, notas ou relatórios PDF, utilize um bucket dedicado no **Google Cloud Storage (GCS)**, concedendo o papel `roles/storage.objectAdmin` à Service Account `atlaserp-sa`.
