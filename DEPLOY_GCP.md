# 🚀 Guia de Implantação em Nuvem — Google Cloud Platform (GCP)

Este documento descreve detalhadamente a arquitetura de infraestrutura e o procedimento determinístico de implantação (*deployment*) do **Atlas ERP** no ecossistema **Google Cloud Platform**.

---

## 🏛️ Topologia e Recursos GCP

A arquitetura em nuvem adota os princípios de *Serverless*, menor privilégio de IAM (*Least Privilege*), alta disponibilidade e isolamento de banco de dados relacional gerenciado:

1. **Google Cloud Run (Compute Layer):**
   - **Serviço Web:** `atlas-erp`
   - **Região:** `southamerica-east1` (São Paulo)
   - **Recursos:** 1 GiB RAM, 1 vCPU, concorrência 8 requisições por container, escalonamento automático de 0 a 5 instâncias.
   - **Comunicação:** Conexão nativa e criptografada via Unix Socket do Cloud SQL Proxy (`/cloudsql/PROJECT:REGION:INSTANCE`).

2. **Google Cloud SQL (Database Layer):**
   - **Instância:** `atlaserp-db`
   - **Engine:** MySQL 8.4 LTS
   - **Banco:** `atlas_erp`
   - **Segurança de Rede:** Acesso restrito a conexões autorizadas via Service Account e Cloud SQL Proxy (sem IP público aberto para a internet).

3. **Google Secret Manager (Secret Management):**
   - `atlaserp_database_url`: String de conexão criptografada com credenciais do banco.
   - `atlaserp_secret_key`: Chave criptográfica mestra para integridade das sessões Flask.
   - `atlaserp_financial_password`: Senha de desbloqueio para áreas financeiras sensíveis.

4. **Artifact Registry & Cloud Build (CI/CD & Container Registry):**
   - Repositório de imagens Docker multi-stage construído e versionado na mesma região do Cloud Run.

---

## 🔐 Service Account e Permissões IAM

Uma conta de serviço dedicada (`atlaserp-sa@PROJECT.iam.gserviceaccount.com`) foi configurada com apenas os papéis mínimos estritamente necessários para operação segura:

- `roles/cloudsql.client`: Permite ao container abrir conexão autenticada com a instância do Cloud SQL.
- `roles/secretmanager.secretAccessor`: Permite ao container ler as versões mais recentes dos segredos em runtime.

---

## ⚙️ Procedimento de Deploy Passo a Passo

### 1. Construção da Imagem Docker
A imagem Docker é compilada a partir do código versionado e enviada ao Artifact Registry:

```bash
gcloud builds submit --tag "${IMAGE_URL}"
```

### 2. Execução das Migrações Estruturais (Alembic / Flask-Migrate)
As migrações de esquema do banco de dados são executadas de forma determinística em um container efêmero isolado (*Cloud Run Job*) antes da inicialização do tráfego web:

```bash
gcloud run jobs execute atlaserp-migrate --region=$REGION --wait
```

### 3. Deploy do Serviço Web no Cloud Run
O serviço web é publicado ou atualizado com as variáveis de ambiente e referências aos segredos montados como variáveis de ambiente em runtime:

```bash
gcloud run deploy atlas-erp \
    --image="${IMAGE_URL}" \
    --region=$REGION \
    --platform=managed \
    --service-account="${SA_EMAIL}" \
    --memory=1Gi \
    --concurrency=8 \
    --max-instances=5 \
    --min-instances=0 \
    --add-cloudsql-instances="${PROJECT_ID}:${REGION}:atlaserp-db" \
    --set-env-vars="FLASK_ENV=production,ERP_EMERGENCY_ADMIN_ENABLED=false,USE_PROXY_FIX=true" \
    --set-secrets="DATABASE_URL=atlaserp_database_url:latest,SECRET_KEY=atlaserp_secret_key:latest,FINANCIAL_ACCESS_PASSWORD=atlaserp_financial_password:latest"
```

### 4. Provisionamento Inicial do Usuário Administrador (Seed RBAC)
O perfil mestre e o usuário inicial são criados no banco de dados através de um Job executado uma única vez:

```bash
gcloud run jobs execute atlaserp-seed-auth --region=$REGION --wait
```

---

## 📈 Resiliência e Escalabilidade

- **Zero-Downtime Deployment:** O Cloud Run utiliza *Blue/Green Revisions* automáticas. Novas versões do container só recebem tráfego após os *Health Checks* de inicialização responderem com sucesso.
- **Auto-Scaling:** Caso o sistema receba picos de requisições, o Cloud Run escala automaticamente até 5 instâncias concorrentes em milissegundos.
- **Fail-Safe Sessions:** Sessões utilizam cookies criptografados stateless compatíveis com qualquer instância do pool sem necessidade de sticky sessions.
