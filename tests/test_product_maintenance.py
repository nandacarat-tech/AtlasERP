from app import create_app, db
from app.models import Product


def make_app():
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
    )

    with app.app_context():
        db.drop_all()
        db.create_all()

    return app


def create_test_product():
    product = Product(
        sku="SKU-001",
        name="Produto de teste",
        price="19.90",
        stock_quantity=10,
    )

    db.session.add(product)
    db.session.commit()

    return product


def test_get_product():
    app = make_app()

    with app.app_context():
        product = create_test_product()
        product_id = product.id

    response = app.test_client().get(f"/products/{product_id}")

    assert response.status_code == 200
    assert response.get_json()["sku"] == "SKU-001"


def test_update_product():
    app = make_app()

    with app.app_context():
        product = create_test_product()
        product_id = product.id

    response = app.test_client().put(
        f"/products/{product_id}",
        json={
            "name": "Produto atualizado",
            "price": "24.90",
            "stock_quantity": 25,
        },
    )

    assert response.status_code == 200

    data = response.get_json()
    assert data["name"] == "Produto atualizado"
    assert data["price"] == "24.90"
    assert data["stock_quantity"] == 25


def test_deactivate_product():
    app = make_app()

    with app.app_context():
        product = create_test_product()
        product_id = product.id

    response = app.test_client().delete(f"/products/{product_id}")

    assert response.status_code == 200
    assert response.get_json()["is_active"] is False
