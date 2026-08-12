# API do AtlasERP

## Convenções

- As respostas usam JSON.
- IDs são inteiros positivos.
- Datas e valores monetários são serializados pelas funções de representação do projeto.
- Erros de validação retornam um objeto com a chave `error`.

## Vendas

### Listar vendas

```http
GET /sales
```

A resposta é uma lista JSON. Filtros opcionais:

```http
GET /sales?status=OPEN
GET /sales?customer_id=1
GET /sales?status=CONFIRMED&customer_id=1
```

Status válidos:

- `OPEN`
- `CONFIRMED`
- `CANCELLED`

Exemplo de erro:

```json
{
  "error": "invalid sale status"
}
```

### Listar vendas com paginação

```http
GET /sales/paginated
```

Parâmetros:

| Parâmetro | Obrigatório | Padrão | Restrições |
|---|---:|---:|---|
| `page` | Não | `1` | Inteiro positivo |
| `per_page` | Não | `10` | Inteiro entre `1` e `100` |
| `status` | Não | — | `OPEN`, `CONFIRMED` ou `CANCELLED` |
| `customer_id` | Não | — | Inteiro positivo |

Exemplo:

```http
GET /sales/paginated?page=2&per_page=10&status=CONFIRMED
```

Resposta:

```json
{
  "items": [],
  "page": 2,
  "per_page": 10,
  "total": 0,
  "pages": 0
}
```

Os campos significam:

- `items`: vendas da página solicitada;
- `page`: página atual;
- `per_page`: quantidade máxima de itens por página;
- `total`: total após aplicação dos filtros;
- `pages`: número total de páginas.

A rota `/sales` permanece sem paginação para preservar compatibilidade com consumidores existentes.

### Consultar uma venda

```http
GET /sales/{sale_id}
```

### Confirmar uma venda

```http
POST /sales/{sale_id}/confirm
```

### Cancelar uma venda

```http
POST /sales/{sale_id}/cancel
```