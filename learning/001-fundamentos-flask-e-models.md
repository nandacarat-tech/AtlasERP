# Apostila 01: Fundamentos da Arquitetura Flask e SQLAlchemy

Bem-vinda à sua primeira apostila didática do **AtlasERP por NandaTech**!

Como você já fez cursos dos fundamentos da linguagem **Python**, vamos construir uma ponte entre o que você aprendeu em Python puro e a estrutura de uma aplicação web real profissional usando **Flask** e **SQLAlchemy**.

---

## 1. O que é o Flask e como ele funciona?

Em Python puro, quando executamos um script (ex: `python script.py`), ele executa de cima para baixo e finaliza. 
No desenvolvimento web, uma aplicação precisa ficar **ouvindo requisições na rede** (por exemplo, quando alguém digita `http://127.0.0.1:5000/` no navegador).

O **Flask** é um *microframework* Python responsável por receber essas requisições HTTP e entregar páginas HTML ou dados em formato JSON.

### A Estrutura do AtlasERP:
- [app/__init__.py](file:///C:/Users/Fernanda/Projetos/AtlasERP/app/__init__.py): Inicializa a aplicação Flask e configura extensões como o banco de dados.
- [app/routes.py](file:///C:/Users/Fernanda/Projetos/AtlasERP/app/routes.py): Define as "Rotas" (URLs que o usuário pode acessar no navegador ou via API).
- [app/models.py](file:///C:/Users/Fernanda/Projetos/AtlasERP/app/models.py): Contém os "Modelos" de dados (as tabelas do banco de dados representadas como classes Python).

---

## 2. Entendendo o SQLAlchemy (ORM)

No desenvolvimento web, o banco de dados guarda informações em tabelas. O **SQLAlchemy** é um **ORM** (*Object-Relational Mapper*), o que significa que ele nos permite manipular o banco de dados usando **classes e objetos Python**, sem precisar escrever comandos SQL brutos.

### Exemplo Didático:
Em vez de escrever SQL puro como:
```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name VARCHAR(150),
    price NUMERIC(10, 2)
);
```

No Python escrevemos a classe:
```python
class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
```

### Operações Básicas (CRUD) em Python:
- **Criar (Create):**
  ```python
  novo_produto = Product(name="Caminhão Scania", price=450000.00)
  db.session.add(novo_produto)
  db.session.commit()
  ```
- **Ler (Read):**
  ```python
  todos_produtos = Product.query.all()
  ```
- **Buscar por ID:**
  ```python
  produto = db.session.get(Product, 1)
  ```

---

## 3. O que são Jinja2 Templates?

O Flask utiliza um mecanismo chamado **Jinja2** para misturar código Python com arquivos HTML.

Por exemplo, no arquivo [app/templates/base.html](file:///C:/Users/Fernanda/Projetos/AtlasERP/app/templates/base.html), usamos blocos como:
```html
{% block content %}
<!-- Conteúdo específico de cada página entra aqui -->
{% endblock %}
```

Nas páginas filhas (como [app/templates/fleet.html](file:///C:/Users/Fernanda/Projetos/AtlasERP/app/templates/fleet.html)), herdamos a estrutura com:
```html
{% extends "base.html" %}
```

Isso garante que o cabeçalho, logotipo e rodapé **NandaTech** apareçam automaticamente em todas as páginas sem precisar repetir código!

---

## 📝 Exercício Didático de Fixação
1. Abra o arquivo [app/models.py](file:///C:/Users/Fernanda/Projetos/AtlasERP/app/models.py) e localize a classe `Driver`.
2. Identifique quais colunas são obrigatórias (`nullable=False`) e quais são opcionais (`nullable=True`).
3. Note como o relacionamento `vehicle_id` conecta o motorista à tabela `fleet_vehicles`.
