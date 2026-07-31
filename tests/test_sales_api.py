from decimal import Decimal

from app import db
from app.customer_models import Customer
from app.models import Product
from app.sale_models import Sale


def create_sale_data():
    customer = Customer(
        document="12345678900",
        name="Cliente da venda",
    )

    product = Product(
        sku="SKU-SALE-001",
        name="Produto vendido",
        price=Decimal("25.00"),
        stock_quantity=10,
    )

    db.session.add_all([customer, product])
    db.session.commit()

    return customer.id, product.id


def test_create_sale(client, app):
    with app.app_context():
        customer_id, product_id = create_sale_data()

    response = client.post(
        "/sales",
        json={
            "customer_id": customer_id,
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 2,
                }
            ],
        },
    )

    assert response.status_code == 201

    data = response.get_json()
    assert data["customer_id"] == customer_id
    assert data["status"] == "OPEN"
    assert data["total_amount"] == "50.00"
    assert data["items"][0]["quantity"] == 2
    assert data["items"][0]["unit_price"] == "25.00"


def test_create_sale_rejects_unknown_customer(client):
    response = client.post(
        "/sales",
        json={
            "customer_id": 9999,
            "items": [
                {
                    "product_id": 1,
                    "quantity": 1,
                }
            ],
        },
    )

    assert response.status_code == 404


def test_create_sale_rejects_insufficient_stock(client, app):
    with app.app_context():
        customer_id, product_id = create_sale_data()

    response = client.post(
        "/sales",
        json={
            "customer_id": customer_id,
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 11,
                }
            ],
        },
    )

    assert response.status_code == 400
    assert "insufficient stock" in response.get_json()["error"]


def test_create_sale_requires_items(client, app):
    with app.app_context():
        customer_id, _ = create_sale_data()

    response = client.post(
        "/sales",
        json={
            "customer_id": customer_id,
            "items": [],
        },
    )

    assert response.status_code == 400


def test_created_sale_is_persisted(client, app):
    with app.app_context():
        customer_id, product_id = create_sale_data()

    response = client.post(
        "/sales",
        json={
            "customer_id": customer_id,
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 3,
                }
            ],
        },
    )

    sale_id = response.get_json()["id"]

    with app.app_context():
        sale = db.session.get(Sale, sale_id)

        assert sale is not None
        assert sale.total_amount == Decimal("75.00")
        assert len(sale.items) == 1

def test_create_sale_rejects_zero_quantity(client, app):
    with app.app_context():
        customer_id, product_id = create_sale_data()

    response = client.post(
        "/sales",
        json={
            "customer_id": customer_id,
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 0,
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "quantity must be greater than zero"


def test_create_sale_rejects_negative_quantity(client, app):
    with app.app_context():
        customer_id, product_id = create_sale_data()

    response = client.post(
        "/sales",
        json={
            "customer_id": customer_id,
            "items": [
                {
                    "product_id": product_id,
                    "quantity": -1,
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "quantity must be greater than zero"

def test_create_sale_rejects_missing_quantity(client, app):
    with app.app_context():
        customer_id, product_id = create_sale_data()

    response = client.post(
        "/sales",
        json={
            "customer_id": customer_id,
            "items": [
                {
                    "product_id": product_id,
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == (
        "product_id and integer quantity are required"
    )


def test_create_sale_rejects_non_integer_quantity(client, app):
    with app.app_context():
        customer_id, product_id = create_sale_data()

    response = client.post(
        "/sales",
        json={
            "customer_id": customer_id,
            "items": [
                {
                    "product_id": product_id,
                    "quantity": "2",
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == (
        "product_id and integer quantity are required"
    )