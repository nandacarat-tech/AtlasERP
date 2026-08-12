# API do AtlasERP

## Convencoes

- As respostas usam JSON.
- IDs sao inteiros positivos.
- Datas e valores monetarios sao serializados pelas funcoes de representacao do projeto.
- Erros de validacao retornam um objeto com a chave `error`.

## Vendas

### Listar vendas

```http
GET /sales
```

A resposta e uma lista JSON. Filtros opcionais:

```http
GET /sales?status=OPEN
GET /sales?customer_id=1
GET /sales?status=CONFIRMED&customer_id=1
```

Status validos:

- `OPEN`
- `CONFIRMED`
- `CANCELLED`

Exemplo de erro:

```json
{
  "error": "invalid sale status"
}
```

### Listar vendas com paginacao

```http
GET /sales/paginated
```

Parametros:

| Parametro | Obrigatorio | Padrao | Restricoes |
|---|---:|---:|---|
| `page` | Nao | `1` | Inteiro positivo |
| `per_page` | Nao | `10` | Inteiro entre `1` e `100` |
| `status` | Nao | `-` | `OPEN`, `CONFIRMED` ou `CANCELLED` |
| `customer_id` | Nao | `-` | Inteiro positivo |

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

- `items`: vendas da pagina solicitada;
- `page`: pagina atual;
- `per_page`: quantidade maxima de itens por pagina;
- `total`: total apos aplicacao dos filtros;
- `pages`: numero total de paginas.

A rota `/sales` permanece sem paginacao para preservar compatibilidade com consumidores existentes.

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
