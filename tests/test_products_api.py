from app import db
from app.models import Product


def test_list_products(client, app):
    with app.app_context():
        db.session.add(Product(
            sku="SKU-001",
            name="Produto de teste",
            price="19.90",
            stock_quantity=10,
        ))
        db.session.commit()

    response = client.get("/products")

    assert response.status_code == 200
    assert len(response.get_json()) == 1
    assert response.get_json()[0]["sku"] == "SKU-001"


def test_create_product(client):
    response = client.post(
        "/products",
        json={
            "sku": "SKU-002",
            "name": "Novo produto",
            "price": "29.90",
            "stock_quantity": 5,
        },
    )

    assert response.status_code == 201
    assert response.get_json()["sku"] == "SKU-002"
    assert response.get_json()["price"] == "29.90"


def test_create_product_rejects_missing_fields(client):
    response = client.post(
        "/products",
        json={"name": "Produto incompleto"},
    )

    assert response.status_code == 400

def test_create_product_rejects_invalid_price(client):
    response = client.post(
        "/products",
        json={
            "sku": "SKU-INVALID-PRICE",
            "name": "Produto inválido",
            "price": "abc",
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "price must be a valid number"


def test_create_product_rejects_negative_price(client):
    response = client.post(
        "/products",
        json={
            "sku": "SKU-NEGATIVE-PRICE",
            "name": "Produto negativo",
            "price": "-1.00",
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "price cannot be negative"


def test_create_product_rejects_duplicate_sku(client, app):
    with app.app_context():
        db.session.add(Product(
            sku="SKU-DUPLICATE",
            name="Produto existente",
            price="10.00",
        ))
        db.session.commit()

    response = client.post(
        "/products",
        json={
            "sku": "SKU-DUPLICATE",
            "name": "Outro produto",
            "price": "20.00",
        },
    )

    assert response.status_code == 409
    assert response.get_json()["error"] == "sku already exists"

def test_create_product_rejects_negative_stock(client):
    response = client.post(
        "/products",
        json={
            "sku": "SKU-NEGATIVE-STOCK",
            "name": "Produto com estoque inválido",
            "price": "10.00",
            "stock_quantity": -1,
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == (
        "stock_quantity cannot be negative"
    )


def test_create_product_rejects_non_integer_stock(client):
    response = client.post(
        "/products",
        json={
            "sku": "SKU-STRING-STOCK",
            "name": "Produto com estoque inválido",
            "price": "10.00",
            "stock_quantity": "10",
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == (
        "stock_quantity must be an integer"
    )