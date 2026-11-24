# Memória do Projeto: NandaTech / Fernanda Caratanasov

Este documento é a fonte única de verdade compartilhada entre todas as conversas e sessões deste projeto no Antigravity.

---

## 1. Visão Geral e Objetivo
- **Nome do Projeto:** NandaTech / Portfólio & Landing Page Corporativa
- **Objetivo Principal:** Apresentar a NandaTech como hub de engenharia de software corporativa, automação inteligente e DevOps, com destaque principal para o **Atlas ERP** em produção e direcionamento de novos negócios e parcerias técnicas.
- **Público / Stakeholders:** Clientes corporativos B2B, gestores de tecnologia, recrutadores tech e parceiros de negócios.

---

## 2. Decisões Acordadas e Diretrizes Fixadas
- **Domínio Principal:** `nandatech.com.br` -> Landing Page Institucional e Vitrine Técnica da NandaTech.
- **Subdomínio do ERP:** `erpatlas.nandatech.com.br` -> Atlas ERP em produção com SSL no Firebase Hosting conectado ao Cloud Run (`southamerica-east1`).
- **Padrões de Design:** Identidade visual oficial NandaTech definida com logotipo Minimalista Executivo (monograma N angular em azul marinho e detalhe ascendente em ciano platina).
- **Visão de Negócios:** Estrutura escalável para múltiplos ERPs verticais MEI sob a marca NandaTech (`erpatlas`, `erpbeauty`, etc.).
- **Botão de Live Demo:** Destaque de conversão na Landing Page direcionando para `erpatlas.nandatech.com.br`.

---

## 3. Log de Conversas e Sessões

### Sessão Inicial (2026-11-02)
- **Tópico:** Inicialização da memória contínua do projeto.
- **O que foi realizado:** Estruturação do repositório de memória compartilhada.

### Sessão de Blindagem de Segurança e Pré-Produção do Atlas ERP (2026-11-11)
- **Tópico:** Resolução dos apontamentos da auditoria de pré-produção do Atlas ERP.
- **O que foi realizado:**
  - Imutabilidade da tabela `audit_logs` no ORM e Engine SQL.
  - Rota `/logout` estritamente POST (405 para GET).
  - ProxyFix configurado (`x_for=1, x_proto=1`) contra IP spoofing.
  - Implementação de `EmergencyAdminIdentity` com escopo restrito.
  - Remoção de verificação de senhas em texto plano; política de senhas fortes.
  - Suíte unificada de 162 testes executada com 100% de sucesso.

### Sessão de Implantação e Produção (2026-11-19)
- **Tópico:** Deploy definitivo no GCP Cloud Run (`southamerica-east1`) + Cloud SQL MySQL 8.4 LTS, povoamento de 500 clientes e frota, registro do domínio `nandatech.com.br`.
- **O que foi realizado:**
  - Produção ativa em `https://atlas-erp-534057493749.southamerica-east1.run.app`.
  - Povoamento massivo de dados reais (clientes, frotas, rotas, NF-e, vendas, compras).
  - Repositório sincronizado em `https://github.com/nandacarat-tech/AtlasERP`.
  - Registro de `nandatech.com.br` no Registro.br.

### Sessão Atual — Identidade Visual, Landing Page e Apontamentos DNS (2026-11-19)
- **Tópico:** Criação do Logotipo Oficial NandaTech, implementação e publicação da nova Landing Page corporativa, apontamento DNS no Registro.br e vinculação ao Firebase Hosting.
- **O que foi realizado:**
  - **Identidade Visual:** Criado e aprovado o Logotipo Oficial NandaTech (Minimalista Executivo & Linear), vetorizado em SVG na Navbar e salvo em alta definição (`nandatech_logo.jpg`).
  - **Landing Page NandaTech:** Desenvolvida e publicada em `nandatech.com.br` via GitHub Pages (`nandacarat-tech/portfolio`) com design B2B premium, vitrine especial do Atlas ERP, alternador Dark/Light e responsividade completa. Testada em `http://localhost:3000`.
  - **DNS no Registro.br:** Configurada a Zona DNS em Modo Avançado com entradas validadas e respondendo ativamente:
    - CNAME `erpatlas` -> `atlas-erp-73956.web.app` (Atlas ERP).
    - Registros A (4 IPs) e CNAME `www` -> GitHub Pages (Landing Page).
  - **Modo Demonstração (Live Demo de 1 Clique) & Proteção Anti-Sabotagem (Opção 1 + 3):**
    - Adicionado botão de destaque "⚡ Entrar com 1 Clique (Demonstração)" em `login.html`.
    - Adicionado suporte a credenciais demo universais (`admin` / `demo`) com preenchimento em 1 clique via chips interativos.
    - Implementado endpoint dedicado `/login/demo` com criação imediata de sessão de Administrador e rastreamento em trilha de auditoria.
    - Implementado desbloqueio em 1 clique para o Módulo Financeiro (`/financial/unlock/demo`) e suporte à senha `demo`.
    - Exibição de indicador de status no cabeçalho do ERP: `🟢 Modo Demonstração • Vitrine NandaTech`.
    - **Proteção Anti-Sabotagem da Vitrine:** Blindagem em `app/routes.py` para impedir que visitantes em sessão demo excluam o acervo original semeado (clientes, produtos base, motoristas, rotas e lançamentos financeiros). Novos cadastros criados pelos visitantes podem ser excluídos normalmente.
    - Suíte de 166 testes automatizados executada e 100% aprovada (`166 passed`).
    - Commits e push realizados com sucesso em `nandacarat-tech/AtlasERP`.

### Sessão de Auditoria Independente, Hardening de Frota, Concorrência e LGPD (2026-11-24)
- **Tópico:** Auditoria defensiva interna (Red Team), remediação de Broken Access Control na frota, mitigação de race condition e inflação de estoque, minimização de dados pessoais (LGPD) e rastreabilidade criptográfica de release em produção.
- **O que foi realizado:**
  - **SEC-01 (Broken Access Control):** Bloqueio estrito de acesso anônimo (`HTTP 401`) em todos os endpoints de frota e devoluções (`/fleet/*`, `/api/fleet/*`). Matriz de RBAC por perfil implementada e testada: `CONSULTA` tem apenas leitura; `VENDEDOR` e `ESTOQUISTA` têm mutações bloqueadas com `403`; `GERENTE` e `ADMIN` possuem acesso operacional.
  - **SEC-02 (Minimização de Dados / LGPD):** Exposição pública eliminada; serialização no backend refatorada para aplicar mascaramento automático de CPF (`***.***.025-**`), CNH (`*******0025`) e telefone para usuários com perfil `CONSULTA`. Perfis com permissão `fleet.manage` (`ADMIN`/`GERENTE`) mantêm acesso completo para gestão de escala e conformidade de trânsito.
  - **SEC-03 (Concorrência e Integridade em Devoluções):** Neutralizado o exploit de inflação de estoque via *Ping-Pong* de status. Implementada trava atômica no banco (`UPDATE delivery_returns SET stock_restored = 1 WHERE id = :id AND stock_restored = 0`), garantindo que apenas uma transação vencedora efetue a reposição. Adicionada validação estrita *all-or-nothing* com `rollback()` caso a venda vinculada ou qualquer um de seus produtos não exista. Teste de concorrência multithread criado e validado.
  - **SEC-04 (Proteção Anti-Sabotagem da Vitrine):** Refatorada a função `is_protected_demo_record` para identificar dinamicamente o acervo original semeado mesmo após re-seeds com IDs superiores. Registros semeados (ex: Rota ID 31) retornam `HTTP 403 Forbidden` com aviso educativo; registros efêmeros criados pelo visitante (ex: Rota ID 59) são excluídos com `HTTP 200 OK`.
  - **Suíte de Testes Automatizada:** Expandida para **207 testes automatizados (100% GREEN / Aprovados)**.
  - **Rastreabilidade de Release em Produção:**
    - Revisão Ativa no Cloud Run: `atlas-erp-00017-9bt`
    - Commit Git de Origem: `ba79c96`
    - Container Image Digest: `southamerica-east1-docker.pkg.dev/atlas-erp-prod-2026/cloud-run-source-deploy/atlas-erp@sha256:b8f1c1eeb4bdc37188c1a15359f39b98c24aa787c0bcf5bfa4434d182602e41c`
    - Status do Tráfego: 100% atendido pela revisão `atlas-erp-00017-9bt`.

---


