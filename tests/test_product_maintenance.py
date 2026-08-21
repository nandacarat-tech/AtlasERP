from app import db
from app.models import Product


def test_get_product(client, app):
    with app.app_context():
        product = Product(
            sku="SKU-GET",
            name="Produto",
            price="10.00",
            is_active=True,
        )
        db.session.add(product)
        db.session.commit()
        product_id = product.id

    response = client.get(f"/products/{product_id}")

    assert response.status_code == 200
    assert response.get_json()["sku"] == "SKU-GET"


def test_update_product(client, app):
    with app.app_context():
        product = Product(
            sku="SKU-UPDATE",
            name="Produto original",
            price="10.00",
            is_active=True,
        )
        db.session.add(product)
        db.session.commit()
        product_id = product.id

    response = client.put(
        f"/products/{product_id}",
        json={
            "name": "Produto atualizado",
            "price": "15.00",
        },
    )

    assert response.status_code == 200
    assert response.get_json()["name"] == "Produto atualizado"


def test_deactivate_product(client, app):
    with app.app_context():
        product = Product(
            sku="SKU-DEACTIVATE",
            name="Produto",
            price="10.00",
            is_active=True,
        )
        db.session.add(product)
        db.session.commit()
        product_id = product.id

    response = client.delete(f"/products/{product_id}")

    assert response.status_code == 200
    assert response.get_json()["is_active"] is False


def test_update_product_preserves_sku(client, app):
    with app.app_context():
        product = Product(
            sku="SKU-PRESERVE",
            name="Produto original",
            price="10.00",
        )
        db.session.add(product)
        db.session.commit()
        product_id = product.id

    response = client.put(
        f"/products/{product_id}",
        json={
            "sku": "SKU-IGNORED",
            "name": "Produto atualizado",
        },
    )

    assert response.status_code == 200
    assert response.get_json()["sku"] == "SKU-PRESERVE"
    assert response.get_json()["name"] == "Produto atualizado"


def test_update_product_rejects_string_is_active(client, app):
    with app.app_context():
        product = Product(
            sku="SKU-BOOLEAN",
            name="Produto",
            price="10.00",
            is_active=True,
        )
        db.session.add(product)
        db.session.commit()
        product_id = product.id

    response = client.put(
        f"/products/{product_id}",
        json={"is_active": "false"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "is_active must be a boolean"


def test_update_product_accepts_boolean_is_active(client, app):
    with app.app_context():
        product = Product(
            sku="SKU-REAL-BOOLEAN",
            name="Produto",
            price="10.00",
            is_active=True,
        )
        db.session.add(product)
        db.session.commit()
        product_id = product.id

    response = client.put(
        f"/products/{product_id}",
        json={"is_active": False},
    )

    assert response.status_code == 200
    assert response.get_json()["is_active"] is False