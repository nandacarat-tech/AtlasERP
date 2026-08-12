# AtlasERP

Sistema ERP modular para operações de atacado e varejo.

## Stack

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- pytest
- SQLite para desenvolvimento

## Configuração do ambiente

Crie e ative o ambiente virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:

```powershell
python -m pip install -r requirements.txt
```

Para configurar variáveis de ambiente, copie o arquivo de exemplo:

```powershell
Copy-Item .env.example .env
```

## Banco de dados e migrações

Para aplicar as migrações no banco configurado:

```powershell
python -m flask --app run.py db upgrade
```

Para verificar a revisão atual:

```powershell
python -m flask --app run.py db current
```

Para verificar se os modelos e as migrações estão sincronizados:

```powershell
python -m flask --app run.py db check
```

Quando houver alteração estrutural nos modelos, gere uma migration:

```powershell
python -m flask --app run.py db migrate -m "descreva a alteração"
```

Revise o arquivo gerado antes de aplicar:

```powershell
python -m flask --app run.py db upgrade
```

## Executar a aplicação

```powershell
python run.py
```

A aplicação ficará disponível em:

```text
http://127.0.0.1:5000
```

## Executar os testes

```powershell
python -m pytest -q
```

A suíte atual cobre criação, consulta, atualização, desativação, estoque, confirmação, cancelamento e listagem paginada de vendas.

## Endpoints principais

### Saúde da aplicação

```http
GET /
```

### Produtos

```http
GET    /products
POST   /products
GET    /products/{product_id}
PUT    /products/{product_id}
PATCH  /products/{product_id}/deactivate
```

### Clientes

```http
GET    /customers
POST   /customers
GET    /customers/{customer_id}
PUT    /customers/{customer_id}
PATCH  /customers/{customer_id}/deactivate
```

### Vendas

```http
GET    /sales
POST   /sales
GET    /sales/{sale_id}
POST   /sales/{sale_id}/confirm
POST   /sales/{sale_id}/cancel
```

## Listagem de vendas

A rota legada mantém uma resposta em formato de lista:

```http
GET /sales
```

Filtros disponíveis:

```http
GET /sales?status=OPEN
GET /sales?customer_id=1
GET /sales?status=CONFIRMED&customer_id=1
```

Os status aceitos são:

- `OPEN`
- `CONFIRMED`
- `CANCELLED`

## Listagem paginada

A rota paginada é:

```http
GET /sales/paginated
```

Parâmetros:

- `page`: página iniciando em `1`; padrão `1`;
- `per_page`: quantidade de registros; padrão `10`;
- limite máximo de `per_page`: `100`;
- `status`: filtro opcional;
- `customer_id`: filtro opcional.

Exemplo:

```http
GET /sales/paginated?page=1&per_page=10&status=CONFIRMED
```

Formato da resposta:

```json
{
  "items": [],
  "page": 1,
  "per_page": 10,
  "total": 0,
  "pages": 0
}
```

A rota `/sales` não foi alterada para preservar compatibilidade com consumidores existentes.

## Documentação adicional

- [Visão geral do projeto](docs/overview.md)
- [Arquitetura](docs/architecture.md)

## Documentação adicional

- [Visão geral do projeto](docs/overview.md)
- [Arquitetura](docs/architecture.md)
- [API](docs/api.md)

