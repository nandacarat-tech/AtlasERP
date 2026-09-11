import pytest
from app import db
from app.models import Product, DeliveryReturn
from app.customer_models import Customer
from app.sale_models import Sale, SaleItem


def test_create_delivery_return(client):
    res = client.post("/api/fleet/returns", json={
        "customer_name": "Empresa ABC Ltda",
        "reason": "CLIENT_ABSENT",
        "attempt_date": "2026-09-11",
        "notes": "Tentativa realizada às 14:30. Portão fechado."
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data["customer_name"] == "Empresa ABC Ltda"
    assert data["reason"] == "CLIENT_ABSENT"
    assert data["status"] == "PENDING_RETURN"


def test_create_delivery_return_validation(client):
    res = client.post("/api/fleet/returns", json={
        "customer_name": "",
        "reason": "CLIENT_ABSENT"
    })
    assert res.status_code == 400
    assert "Nome do cliente" in res.get_json()["error"]

    res2 = client.post("/api/fleet/returns", json={
        "customer_name": "Cliente Teste",
        "reason": ""
    })
    assert res2.status_code == 400
    assert "Motivo" in res2.get_json()["error"]


def test_list_and_filter_delivery_returns(client):
    client.post("/api/fleet/returns", json={
        "customer_name": "Cliente Filtro 1",
        "reason": "ADDRESS_NOT_FOUND",
        "status": "PENDING_RETURN"
    })
    client.post("/api/fleet/returns", json={
        "customer_name": "Cliente Filtro 2",
        "reason": "CARGO_DAMAGED",
        "status": "RETURNED_TO_STOCK"
    })

    res_all = client.get("/api/fleet/returns")
    assert res_all.status_code == 200
    assert len(res_all.get_json()) >= 2

    res_pending = client.get("/api/fleet/returns?status=PENDING_RETURN")
    assert res_pending.status_code == 200
    for item in res_pending.get_json():
        assert item["status"] == "PENDING_RETURN"

    res_damaged = client.get("/api/fleet/returns?reason=CARGO_DAMAGED")
    assert res_damaged.status_code == 200
    for item in res_damaged.get_json():
        assert item["reason"] == "CARGO_DAMAGED"


def test_resolve_delivery_return_with_stock_restoration(client, app):
    with app.app_context():
        # Criar cliente
        customer = Customer(
            name="Cliente Retorno",
            document="999.888.777-66",
            email="retorno@cliente.com"
        )
        db.session.add(customer)
        db.session.commit()

        # Criar produto com estoque inicial 10
        product = Product(
            sku="PROD-RET-01",
            name="Monitor LED 27",
            price="1200.00",
            stock_quantity=10,
            minimum_stock=2
        )
        db.session.add(product)
        db.session.commit()
        prod_id = product.id

        # Criar venda com 3 itens
        sale = Sale(customer_id=customer.id, total_amount="3600.00", status="CONFIRMED")
        db.session.add(sale)
        db.session.commit()

        sale_item = SaleItem(sale_id=sale.id, product_id=prod_id, quantity=3, unit_price="1200.00")
        db.session.add(sale_item)
        db.session.commit()
        sale_id = sale.id

    # Criar ocorrência de entrega mal-sucedida
    res_create = client.post("/api/fleet/returns", json={
        "customer_name": "Cliente Retorno",
        "sale_id": sale_id,
        "reason": "CLIENT_REFUSED",
        "notes": "Cliente recusou por desistência."
    })
    assert res_create.status_code == 201
    return_id = res_create.get_json()["id"]

    # Resolver ocorrência alterando status para RETURNED_TO_STOCK
    res_resolve = client.post(f"/api/fleet/returns/{return_id}/resolve", json={
        "status": "RETURNED_TO_STOCK",
        "action_taken": "Mercadoria retornada ao estoque da matriz."
    })
    assert res_resolve.status_code == 200
    assert res_resolve.get_json()["status"] == "RETURNED_TO_STOCK"

    # Verificar se o estoque do produto aumentou de 10 para 13
    with app.app_context():
        p = db.session.get(Product, prod_id)
        assert p.stock_quantity == 13


def test_fleet_returns_summary(client):
    res = client.get("/api/fleet/returns/summary")
    assert res.status_code == 200
    data = res.get_json()
    assert "total" in data
    assert "pending" in data
    assert "returned_to_stock" in data
