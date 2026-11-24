import pytest
from decimal import Decimal

from app import db
from app.models import Product
from app.customer_models import Customer
from app.supplier_models import Supplier
from app.audit_models import AuditLog


def setup_base_data(app):
    with app.app_context():
        customer = Customer.query.filter_by(document="52998224725").first()
        if not customer:
            customer = Customer(
                document="52998224725",
                name="Cliente Teste RBAC",
                email="cliente@rbac.com",
            )
            db.session.add(customer)

        supplier = Supplier.query.filter_by(document="11222333000181").first()
        if not supplier:
            supplier = Supplier(
                document="11222333000181",
                name="Fornecedor Teste RBAC",
                email="fornecedor@rbac.com",
            )
            db.session.add(supplier)

        product = Product.query.filter_by(sku="SKU-RBAC-01").first()
        if not product:
            product = Product(
                sku="SKU-RBAC-01",
                name="Produto RBAC Teste",
                price=Decimal("100.00"),
                stock_quantity=50,
                minimum_stock=5,
            )
            db.session.add(product)

        db.session.commit()
        return customer.id, supplier.id, product.id


def test_anonymous_access_blocked_with_401(app, unauthenticated_client):
    """Requisições anônimas a rotas operacionais devem retornar 401 Unauthorized"""
    customer_id, supplier_id, product_id = setup_base_data(app)

    # Tentativa de criar venda sem login
    res_sale = unauthenticated_client.post("/sales", json={
        "customer_id": customer_id,
        "items": [{"product_id": product_id, "quantity": 1}],
    })
    assert res_sale.status_code == 401

    # Tentativa de criar compra sem login
    res_purchase = unauthenticated_client.post("/purchases", json={
        "supplier_id": supplier_id,
        "items": [{"product_id": product_id, "quantity": 10, "unit_cost": "50.00"}],
    })
    assert res_purchase.status_code == 401

    # Tentativa de criar produto sem login
    res_prod = unauthenticated_client.post("/products", json={
        "sku": "SKU-ANON-01",
        "name": "Produto Anonimo",
        "price": "20.00",
    })
    assert res_prod.status_code == 401


def test_consulta_role_cannot_modify_resources(app, client_factory):
    """Perfil CONSULTA tem permissão apenas de leitura (view) e é bloqueado em mutações (403)"""
    customer_id, supplier_id, product_id = setup_base_data(app)
    client_consulta = client_factory("CONSULTA")

    # Leitura é permitida
    res_get_products = client_consulta.get("/products")
    assert res_get_products.status_code == 200

    res_get_sales = client_consulta.get("/sales")
    assert res_get_sales.status_code == 200

    # Criação de venda é bloqueada
    res_sale = client_consulta.post("/sales", json={
        "customer_id": customer_id,
        "items": [{"product_id": product_id, "quantity": 1}],
    })
    assert res_sale.status_code == 403
    assert "Acesso negado" in res_sale.get_json()["error"]
    assert res_sale.get_json()["required_permission"] == "sales.create"

    # Criação de produto é bloqueada
    res_prod = client_consulta.post("/products", json={
        "sku": "SKU-CONSULTA-01",
        "name": "Produto Bloqueado",
        "price": "30.00",
    })
    assert res_prod.status_code == 403
    assert res_prod.get_json()["required_permission"] == "products.manage"


def test_vendedor_role_boundary(app, client_factory):
    """Perfil VENDEDOR pode criar vendas, mas é bloqueado ao tentar criar compras ou alterar produtos"""
    customer_id, supplier_id, product_id = setup_base_data(app)
    client_vendedor = client_factory("VENDEDOR")

    # VENDEDOR consegue criar venda (sales.create concedida)
    res_sale = client_vendedor.post("/sales", json={
        "customer_id": customer_id,
        "items": [{"product_id": product_id, "quantity": 1}],
    })
    assert res_sale.status_code == 201

    # VENDEDOR é bloqueado ao tentar criar ordem de compra (purchases.create negada)
    res_purchase = client_vendedor.post("/purchases", json={
        "supplier_id": supplier_id,
        "items": [{"product_id": product_id, "quantity": 5, "unit_cost": "40.00"}],
    })
    assert res_purchase.status_code == 403
    assert res_purchase.get_json()["required_permission"] == "purchases.create"

    # VENDEDOR é bloqueado ao tentar cadastrar produtos (products.manage negada)
    res_prod = client_vendedor.post("/products", json={
        "sku": "SKU-VEND-01",
        "name": "Produto por Vendedor",
        "price": "45.00",
    })
    assert res_prod.status_code == 403


def test_estoquista_role_boundary(app, client_factory):
    """Perfil ESTOQUISTA pode gerenciar produtos e estoque, mas é bloqueado ao tentar criar vendas"""
    customer_id, supplier_id, product_id = setup_base_data(app)
    client_estoquista = client_factory("ESTOQUISTA")

    # ESTOQUISTA pode cadastrar produtos (products.manage concedida)
    res_prod = client_estoquista.post("/products", json={
        "sku": "SKU-ESTOQUE-01",
        "name": "Item Estoque Valido",
        "price": "55.00",
        "stock_quantity": 10,
    })
    assert res_prod.status_code == 201

    # ESTOQUISTA é bloqueado ao tentar criar venda (sales.create negada)
    res_sale = client_estoquista.post("/sales", json={
        "customer_id": customer_id,
        "items": [{"product_id": product_id, "quantity": 1}],
    })
    assert res_sale.status_code == 403
    assert res_sale.get_json()["required_permission"] == "sales.create"


def test_audit_log_records_unauthorized_attempts(app, client_factory):
    """Tentativas não autorizadas devem gerar evento UNAUTHORIZED_ACCESS na trilha de auditoria"""
    customer_id, _, product_id = setup_base_data(app)
    client_consulta = client_factory("CONSULTA")

    # Dispara tentativa não autorizada
    client_consulta.post("/sales", json={
        "customer_id": customer_id,
        "items": [{"product_id": product_id, "quantity": 1}],
    })

    with app.app_context():
        log = AuditLog.query.filter_by(
            action="UNAUTHORIZED_ACCESS",
            entity_type="Permission",
            entity_id="sales.create",
        ).order_by(AuditLog.id.desc()).first()

        assert log is not None
        assert log.username_snapshot == "user_consulta"
