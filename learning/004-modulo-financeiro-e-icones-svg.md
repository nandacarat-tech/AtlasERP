# Apostila 04: Módulo Financeiro Completo e Ícones SVG Vetoriais

Bem-vinda à Quarta Apostila do **AtlasERP por NandaTech**!

Nesta aula, avançamos para um dos pilares mais estratégicos de qualquer ERP empresarial: o **Módulo Financeiro**, acompanhado da modernização visual com **Ícones SVG Vetoriais**.

---

## 1. Por que Ícones SVG em vez de Emojis?

Emojis dependem da renderização do sistema operacional do usuário (Windows, Mac, Android ou iOS exibem emojis diferentes). 

Os **Ícones SVG (Scalable Vector Graphics)** são gráficos vetoriais codificados em XML/HTML. Eles trazem as seguintes vantagens:
- **Padronização:** A mesma aparência perfeita e limpa em qualquer dispositivo.
- **Alta Resolução:** Não perdem qualidade em telas retina ou de alta densidade.
- **Estilização Dinâmica:** Podem mudar de cor via CSS usando `stroke="currentColor"`.

---

## 2. A Estrutura do Módulo Financeiro

No arquivo [app/financial_models.py](file:///C:/Users/Fernanda/Projetos/AtlasERP/app/financial_models.py), criamos 3 modelos fundamentais:

### A) Categorias Financeiras (`FinancialCategory`)
Permite classificar as movimentações em 4 grandes grupos:
- **Custos Fixos (`FIXED_COST`):** Aluguel, energia elétrica, internet, assinaturas de software.
- **Custos Variáveis (`VARIABLE_COST`):** Matéria-prima, insumos de produção, frete.
- **Custos de Pessoal (`PAYROLL`):** Folha de pagamento, salários e benefícios.
- **Receitas (`REVENUE`):** Faturamento com vendas e prestação de serviços.

### B) Lançamentos e Contas (`FinancialTransaction`)
Controla o **Fluxo de Caixa** e as **Contas a Pagar / Receber**.
- Contém o status (`PENDING` para contas a vencer, `PAID` para contas quitadas).
- Permite calcular o saldo em tempo real no servidor Flask.

### C) Custos de Pessoal / Folha (`PayrollExpense`)
Gerencia o custo total de cada colaborador da empresa:
- `total_cost = base_salary + charges_amount + benefits_amount`

---

## 3. Como o Python calcula o DRE Resumido

No arquivo [app/routes.py](file:///C:/Users/Fernanda/Projetos/AtlasERP/app/routes.py), criamos a função de resumo `/api/financial/summary`:

```python
net_result = total_revenue - (total_expenses + total_payroll)
```

Essa linha de código traduz o **Resultado Líquido da Empresa**: se o valor for positivo, a empresa teve lucro; se for negativo, aponta a necessidade de ajustar os custos fixos ou aumentar o faturamento.

---

## 📝 Exercício Didático de Fixação
1. Abra a página `http://127.0.0.1:5000/ui/financial/transactions` no seu navegador.
2. Cadastre uma despesa de **Aluguel** (ex: R$ 2.500,00) com status **Pendente**.
3. Observe como o valor aparece em **Contas a Pagar (A Vencer)** no Painel Financeiro e, ao clicar em "Marcar Pago", o valor é computado no DRE!
