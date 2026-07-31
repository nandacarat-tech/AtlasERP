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


def test_list_products():
    app = make_app()

    with app.app_context():
        db.session.add(Product(
            sku="SKU-001",
            name="Produto de teste",
            price="19.90",
            stock_quantity=10,
        ))
        db.session.commit()

    client = app.test_client()
    response = client.get("/products")

    assert response.status_code == 200
    assert len(response.get_json()) == 1
    assert response.get_json()[0]["sku"] == "SKU-001"


def test_create_product():
    app = make_app()
    client = app.test_client()

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


def test_create_product_rejects_missing_fields():
    app = make_app()
    client = app.test_client()

    response = client.post(
        "/products",
        json={"name": "Produto incompleto"},
    )

    assert response.status_code == 400
