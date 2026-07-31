# Arquitetura do AtlasERP

## Visão geral

O AtlasERP é uma aplicação web construída com Flask, organizada em módulos de configuração, modelos de dados, rotas HTTP e testes automatizados.

## Fluxo da aplicação

```text
Cliente HTTP
    ↓
Rotas Flask
    ↓
Validação das regras de negócio
    ↓
Modelos SQLAlchemy
    ↓
Banco de dados
    ↓
Resposta JSON
```

## Componentes

### `app/__init__.py`

Inicializa a aplicação Flask, configura o banco de dados e registra as rotas.

### `app/config.py`

Centraliza as configurações da aplicação, incluindo a conexão com o banco de dados e as opções de teste.

### `app/routes.py`

Contém os endpoints HTTP e parte das regras de negócio da aplicação.

As rotas atuais abrangem:

- clientes;
- produtos;
- manutenção de produtos;
- vendas;
- confirmação de vendas.

### `app/models.py`

Define o modelo de produto e seus dados persistidos, incluindo:

- SKU;
- nome;
- preço;
- quantidade em estoque.

### `app/customer_models.py`

Define o modelo de cliente e o estado de atividade do cliente.

### `app/sale_models.py`

Define os modelos de venda e item de venda, incluindo os relacionamentos entre:

- cliente e venda;
- venda e itens;
- item e produto.

## Fluxo de uma venda

### Criação

A API recebe o cliente e os itens da venda. As entradas são validadas antes da persistência.

### Confirmação

Na confirmação:

1. a venda é carregada;
2. o status é verificado;
3. todos os itens são validados;
4. o estoque disponível é conferido;
5. o estoque é reduzido;
6. a venda recebe o status `CONFIRMED`;
7. as alterações são persistidas.

A validação de todos os itens ocorre antes da baixa do estoque. Assim, uma venda inválida não reduz parcialmente o estoque.

## Testes

Os testes ficam no diretório `tests/` e cobrem:

- inicialização da aplicação;
- modelos;
- clientes;
- produtos;
- manutenção de produtos;
- criação de vendas;
- validação de itens;
- confirmação e baixa de estoque.

A suíte deve ser executada com:

```powershell
python -m pytest -q
```

## Princípios atuais

- validação antes da alteração de dados;
- operações de estoque atomicamente verificadas;
- regras importantes protegidas por testes;
- commits pequenos e descritivos;
- documentação mantida junto do código.