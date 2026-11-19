# MemÃ³ria do Projeto: atlas_erp

Este documento Ã© a fonte Ãºnica de verdade compartilhada entre todas as conversas e sessÃµes deste projeto no Antigravity.

---

## 1. VisÃ£o Geral e Objetivo
- **Nome do Projeto:** atlas_erp
- **Objetivo Principal:** [Definir objetivo central do projeto]
- **PÃºblico / Stakeholders:** [Identificar pÃºblico ou usuÃ¡rios-alvo]

---

## 2. DecisÃµes Acordadas e Diretrizes Fixadas
- **PadrÃµes & Estilo:** [Diretrizes de design, tom de voz, regras de cÃ³digo ou arquitetura]
- **Identidade / Marca:** [Cores, fontes, logos ou formatos definidos]

---

## 3. Log de Conversas e SessÃµes

### SessÃ£o Inicial (2026-11-02)
- **TÃ³pico:** InicializaÃ§Ã£o da memÃ³ria contÃ­nua do projeto.
- **O que foi realizado:** EstruturaÃ§Ã£o do repositÃ³rio de memÃ³ria compartilhada para suportar mÃºltiplas conversas integradas.
- **PrÃ³ximos Passos:** Registrar novas tarefas e tÃ³picos conforme novas conversas forem iniciadas.

### Sessão de Blindagem de Segurança e Pré-Produção (2026-11-11)
- **Tópico:** Resolução dos apontamentos da auditoria de pré-produção do Atlas ERP.
- **O que foi realizado:**
  - Imutabilidade da tabela `audit_logs` garantida em nível de ORM e de `Engine` (interceptador de mutações SQL DML protegendo contra UPDATE/DELETE, preservando DDLs de criação de tabelas).
  - Rota `/logout` estritamente via POST com retorno de 405 Method Not Allowed para GET.
  - ProxyFix reconfigurado com granularidade restrita (`x_for=1, x_proto=1`) contra IP spoofing.
  - Implementação de `EmergencyAdminIdentity` com escopo restrito a recuperação de desastres (`users.*`, `audit.view`) e bloqueio de aprovações financeiras (`financial.approve`).
  - Remoção de verificação de senhas em texto plano; exigência estrita de hash e política mínima de 12 caracteres.
  - Preservação de espaços válidos em senhas no login e mitigação de enumeração de contas com resposta padronizada.
  - Suíte unificada de 162 testes executada com 100% de sucesso tanto em SQLite local quanto em MySQL 9.7 local.
- **Próximos Passos:** Concluída e aprovada a fase de auditoria de arquitetura e código (162 testes verdes no SQLite e MySQL). Iniciar o ciclo de Homologação (Staging Gate) no GCP Cloud Run com `--no-allow-unauthenticated` e Cloud SQL conforme o roteiro consolidado em `DEPLOY_GCP.md`.

### Sessão de Implantação, Produção e Hardening (2026-11-19)
- **Tópico:** Deploy definitivo no GCP, provisionamento do usuário Admin, povoamento de dados de alta escala (500 clientes e frota massiva), correção de endpoints de frota e registro do domínio de negócio.
- **O que foi realizado:**
  - Implantação bem-sucedida no Cloud Run (`atlas-erp-534057493749.southamerica-east1.run.app`) e Cloud SQL MySQL 8.4 LTS.
  - Configuração de políticas de segurança IAM (`allUsers` com `roles/run.invoker`, Service Account `atlaserp-sa`).
  - Execução bem-sucedida do Job de inicialização RBAC (`atlaserp-seed-auth`) e validação do login do usuário `admin`.
  - Povoamento massivo de dados (`seed_db.py`):
    - 500 Clientes reais (250 B2B com CNPJ válido e 250 B2C com CPF válido, múltiplos DDDs e e-mails únicos).
    - 30 Veículos de frota comercial e pesada (27 operacionais ativos e 3 em manutenção).
    - 25 Motoristas qualificados com CNHs (B, C, D e E) e 25 rotas de entrega pelo Brasil (15 em andamento `IN_PROGRESS`).
    - 60 Vendas com itens e 45 Notas Fiscais eletrônicas (NF-e SEFAZ).
    - 15 Compras de suprimentos, 10 colaboradores na folha de pagamento e lançamentos financeiros (DRE).
  - Correção no backend (`app/routes.py`):
    - Filtro do Dashboard ajustado para somar veículos operacionais (`AVAILABLE` e `IN_USE`).
    - Implementação dos endpoints `/api/fleet/vehicles/summary`, `/api/fleet/drivers/count`, `/api/fleet/routes/active/count` para alimentar dinamicamente os cards de `/ui/fleet`.
  - Todos os commits e documentações de engenharia de nuvem (`DEPLOY_GCP.md` e `README.md` padrão sênior) sincronizados no GitHub (`nandacarat-tech/AtlasERP`).
  - **Registro de Domínio:** Registrado com sucesso o domínio **`nandatech.com.br`** no Registro.br.
  - **Decisão Estratégica de Negócio:**
    - **`erp.nandatech.com.br`**: Subdomínio dedicado para o Atlas ERP em produção.
    - **`nandatech.com.br`**: Domínio principal para a Landing Page corporativa da NandaTech / Portfólio Executivo, com vitrine de projetos e botão de Live Demo para o Atlas ERP.

---

## 4. Estado Atual e Próximos Passos para a Próxima Sessão (Domínio & Landing Page)

- **Repositório GitHub:** `https://github.com/nandacarat-tech/AtlasERP` (Branch `main` atualizada).
- **Ambiente de Produção Atual:** `https://atlas-erp-534057493749.southamerica-east1.run.app`
- **Domínio Registrado:** `nandatech.com.br`
- **Tarefas para a Próxima Sessão:**
  1. Concluir o apontamento DNS de `erp.nandatech.com.br` no Registro.br (CNAME `erp` para `ghs.googlehosted.com.`) e validação SSL.
  2. Desenhar e implementar a **Landing Page Profissional NandaTech** para o domínio raiz `nandatech.com.br`, com foco de negócio/portfólio, destaque para o Atlas ERP e estrutura expansível para futuros projetos.



---

