# Apostila 05: Automação Integrada do ERP e Notas Fiscais Eletrônicas (NF-e / SEFAZ)

Bem-vinda à Quinta Apostila do **AtlasERP por NandaTech**!

Nesta aula, exploramos o conceito central de um ERP moderno: **A Integração e Automação 100% entre os Departamentos**, conectando a operação comercial (Vendas) e de suprimentos (Compras) diretamente ao **Módulo Financeiro** e à **Emissão de Notas Fiscais Eletrônicas (NF-e)**.

---

## 1. O Conceito de Automação de Processos Empresariais (Workflow Autônomo)

Em empresas sem ERP integrados, cada setor opera como uma "ilha isolada". Quando uma venda é concluída:
- O vendedor precisa mandar uma mensagem para o setor financeiro emitir o boleto.
- Precisa avisar o almoxarifado para separar o produto do estoque.
- Precisa solicitar a emissão manual da Nota Fiscal no sistema da prefeitura ou SEFAZ.

No **AtlasERP**, automatizamos todo esse fluxo no backend em Python (`app/routes.py`):

1. **Ao Confirmar uma Venda (`confirm_sale`):**
   - O estoque do produto é **debitado automaticamente**.
   - É criado um registro em **Contas a Receber** no módulo Financeiro.
   - É gerada uma **Nota Fiscal Eletrônica (NF-e)** com status `PENDING_EMISSION` pronta para transmissão à SEFAZ.

2. **Ao Cadastrar uma Compra (`create_purchase`):**
   - A entrada do produto **abastece o estoque automaticamente**.
   - É gerada uma conta em **Contas a Pagar** para controle de custo pelo Financeiro.

---

## 2. A Estrutura da Nota Fiscal Eletrônica (NF-e)

A **NF-e (Nota Fiscal Eletrônica)** é um documento digital regulamentado pela Secretaria da Fazenda (**SEFAZ**) no Brasil. No arquivo [app/financial_models.py](file:///C:/Users/Fernanda/Projetos/AtlasERP/app/financial_models.py), estruturamos o modelo `Invoice` para simular o padrão real:

### A) A Chave de Acesso de 44 Dígitos
Toda NF-e possui uma chave de acesso única formada por 44 números que identifica a nota em todo o território nacional:
- **UF (2 dígitos):** Código do estado (ex: `35` para São Paulo).
- **AAMM (4 dígitos):** Ano e mês da emissão (ex: `2609`).
- **CNPJ da Empresa (14 dígitos):** Identificador fiscal do emissor.
- **Modelo (2 dígitos):** `55` para NF-e de mercadorias.
- **Série (3 dígitos):** `001`.
- **Número da Nota (9 dígitos):** Sequencial único.
- **Tipo de Emissão (1 dígito):** `1` (Normal).
- **Código Numérico Aleatório (8 dígitos):** Segurança contra fraudes.
- **Dígito Verificador - DV (1 dígito):** Calculado pelo algoritmo Módulo 11.

### B) Códigos de Status da SEFAZ
Ao transmitir uma NF-e para a SEFAZ, o servidor fiscal retorna um código estandardizado de resposta:
- `100 - Autorizado o uso da NF-e`: Nota validada e transmitida com sucesso.
- `101 - Cancelamento de NF-e homologado`: Nota devidamente cancelada.
- `539 - Rejeição: Duplicidade de NF-e`: Nota com mesmo número/série já existente.

---

## 3. O Simulador SEFAZ no AtlasERP

No backend do AtlasERP, implementamos o endpoint `/api/financial/invoices/<id>/emit` que:
1. Gera a **Chave de Acesso de 44 dígitos** formatada dinamicamente.
2. Comunica com o simulador fiscal e atualiza o status para `AUTHORIZED` com o código `100 - Autorizado o uso da NF-e`.
3. Registra a data e hora exata da autorização fiscal.

---

## 📝 Exercício Didático de Fixação

1. Acesse o sistema em `http://127.0.0.1:5000/ui/sales`.
2. Escolha um orçamento em aberto e clique no botão **Confirmar Venda**.
3. Acesse a nova página **Financeiro -> Notas Fiscais (NF-e)** em `http://127.0.0.1:5000/ui/financial/invoices`.
4. Observe que a NF-e da sua venda já foi criada automaticamente com status **Pendente de Emissão**.
5. Clique em **Transmitir SEFAZ** e veja a mágica acontecer: a Chave de Acesso de 44 dígitos é gerada e a nota é **Autorizada** instantaneamente!
