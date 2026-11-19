from app import db
from app.auth_models import Role, Permission, User


DEFAULT_PERMISSIONS = [
    # Vendas
    {"code": "sales.view", "module": "Vendas", "description": "Visualizar pedidos de vendas"},
    {"code": "sales.create", "module": "Vendas", "description": "Criar novos pedidos de vendas"},
    {"code": "sales.cancel", "module": "Vendas", "description": "Cancelar vendas existentes"},

    # Compras
    {"code": "purchases.view", "module": "Compras", "description": "Visualizar pedidos de compras"},
    {"code": "purchases.create", "module": "Compras", "description": "Criar ordens de compra"},
    {"code": "purchases.cancel", "module": "Compras", "description": "Cancelar ordens de compra"},

    # Estoque
    {"code": "stock.view", "module": "Estoque", "description": "Consultar saldo e extrato de estoque"},
    {"code": "stock.adjust", "module": "Estoque", "description": "Realizar ajustes manuais de estoque"},

    # Produtos
    {"code": "products.view", "module": "Cadastros", "description": "Visualizar catalogo de produtos"},
    {"code": "products.manage", "module": "Cadastros", "description": "Cadastrar e editar produtos"},

    # Clientes e Fornecedores
    {"code": "customers.view", "module": "Cadastros", "description": "Visualizar clientes"},
    {"code": "customers.manage", "module": "Cadastros", "description": "Cadastrar e editar clientes"},
    {"code": "suppliers.view", "module": "Cadastros", "description": "Visualizar fornecedores"},
    {"code": "suppliers.manage", "module": "Cadastros", "description": "Cadastrar e editar fornecedores"},

    # Financeiro
    {"code": "financial.view", "module": "Financeiro", "description": "Visualizar transacoes e relatorios financeiros"},
    {"code": "financial.manage", "module": "Financeiro", "description": "Cadastrar, liquidar e gerenciar titulos financeiros"},

    # Administracao & Seguranca
    {"code": "users.manage", "module": "Segurança", "description": "Cadastrar, editar e bloquear usuarios e perfis"},
    {"code": "audit.view", "module": "Segurança", "description": "Visualizar a trilha de auditoria do sistema"},
]

ROLE_MATRIX = {
    "ADMIN": [p["code"] for p in DEFAULT_PERMISSIONS],
    "GERENTE": [
        "sales.view", "sales.create", "sales.cancel",
        "purchases.view", "purchases.create", "purchases.cancel",
        "stock.view", "stock.adjust",
        "products.view", "products.manage",
        "customers.view", "customers.manage",
        "suppliers.view", "suppliers.manage",
        "financial.view", "audit.view",
    ],
    "VENDEDOR": [
        "sales.view", "sales.create",
        "products.view", "customers.view", "customers.manage",
    ],
    "ESTOQUISTA": [
        "stock.view", "stock.adjust",
        "products.view", "products.manage",
    ],
    "FINANCEIRO": [
        "financial.view", "financial.manage",
        "sales.view", "purchases.view",
    ],
    "CONSULTA": [
        "sales.view", "purchases.view", "stock.view",
        "products.view", "customers.view", "suppliers.view",
    ],
}


def seed_rbac():
    """
    Popula o banco com os perfis e permissoes padrao se ainda nao existirem.
    Retorna o dicionario de roles criadas/carregadas.
    """
    created_perms = {}
    for p_data in DEFAULT_PERMISSIONS:
        perm = Permission.query.filter_by(code=p_data["code"]).first()
        if not perm:
            perm = Permission(**p_data)
            db.session.add(perm)
        created_perms[p_data["code"]] = perm

    db.session.flush()

    created_roles = {}
    for role_name, perm_codes in ROLE_MATRIX.items():
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role(name=role_name, description=f"Perfil padrao {role_name}")
            db.session.add(role)
        role.permissions = [created_perms[code] for code in perm_codes if code in created_perms]
        created_roles[role_name] = role

    db.session.commit()
    return created_roles
