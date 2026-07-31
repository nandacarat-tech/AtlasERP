# Visão geral do AtlasERP

O AtlasERP é uma aplicação web em Flask para gerenciamento de clientes, produtos, vendas e estoque.

## Módulos atuais

### Clientes

Permite cadastrar e consultar clientes. Vendas só podem ser abertas para clientes ativos.

### Produtos

Permite cadastrar e consultar produtos, incluindo preço, SKU e quantidade em estoque.

### Vendas

Uma venda possui:

- cliente;
- status;
- itens;
- quantidade de cada produto;
- preço unitário;
- total calculado.

O fluxo atual da venda é:

1. criação da venda com status `OPEN`;
2. validação dos itens;
3. confirmação da venda;
4. baixa do estoque;
5. alteração do status para `CONFIRMED`.

## Regras importantes

- clientes inativos não podem realizar vendas;
- produtos inexistentes são rejeitados;
- quantidades devem ser válidas;
- uma venda com múltiplos itens deve ser validada de forma atômica;
- estoque insuficiente impede a confirmação;
- o estoque só é reduzido na confirmação;
- uma venda já confirmada não pode ser confirmada novamente.

## Testes

A suíte automatizada está localizada em `tests/`.

Para executar todos os testes:

```powershell
python -m pytest -q
```

Estado atual: **31 testes passando**.

## Estrutura principal

- `app/routes.py`: rotas HTTP e regras de aplicação;
- `app/models.py`: modelo de produtos;
- `app/customer_models.py`: modelo de clientes;
- `app/sale_models.py`: modelos de vendas e itens;
- `tests/`: testes unitários e de API;
- `migrations/`: histórico de alterações do banco de dados.