from decimal import Decimal

from app import db
from app.customer_models import Customer
from app.models import Product
from app.sale_models import Sale, SaleItem
from app.sale_status import CANCELLED, CONFIRMED, OPEN


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

def test_create_sale_rejects_unknown_product(client, app):
    with app.app_context():
        customer_id, _ = create_sale_data()

    response = client.post(
        "/sales",
        json={
            "customer_id": customer_id,
            "items": [
                {
                    "product_id": 9999,
                    "quantity": 1,
                }
            ],
        },
    )

    assert response.status_code == 404
    assert response.get_json()["error"] == "product not found"

def test_create_sale_rejects_inactive_customer(client, app):
    with app.app_context():
        customer_id, product_id = create_sale_data()

        customer = db.session.get(Customer, customer_id)
        customer.is_active = False
        db.session.commit()

    response = client.post(
        "/sales",
        json={
            "customer_id": customer_id,
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 1,
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "customer is inactive"

def test_create_sale_does_not_change_stock_when_one_item_is_insufficient(
    client, app
):
    with app.app_context():
        customer = Customer(
            document="98765432100",
            name="Cliente atomicidade",
        )

        first_product = Product(
            sku="SKU-ATOMIC-001",
            name="Primeiro produto",
            price=Decimal("10.00"),
            stock_quantity=5,
        )

        second_product = Product(
            sku="SKU-ATOMIC-002",
            name="Segundo produto",
            price=Decimal("20.00"),
            stock_quantity=1,
        )

        db.session.add_all([customer, first_product, second_product])
        db.session.commit()

        customer_id = customer.id
        first_product_id = first_product.id
        second_product_id = second_product.id

    response = client.post(
        "/sales",
        json={
            "customer_id": customer_id,
            "items": [
                {
                    "product_id": first_product_id,
                    "quantity": 2,
                },
                {
                    "product_id": second_product_id,
                    "quantity": 2,
                },
            ],
        },
    )

    assert response.status_code == 400
    assert "insufficient stock" in response.get_json()["error"]

    with app.app_context():
        first_product = db.session.get(Product, first_product_id)
        second_product = db.session.get(Product, second_product_id)

        assert first_product.stock_quantity == 5
        assert second_product.stock_quantity == 1
        assert Sale.query.count() == 0

def test_create_sale_with_multiple_items_updates_total_and_stock(client, app):
    with app.app_context():
        customer = Customer(
            document="11223344556",
            name="Cliente múltiplos itens",
        )

        first_product = Product(
            sku="SKU-MULTI-001",
            name="Produto múltiplo 1",
            price=Decimal("10.00"),
            stock_quantity=8,
        )

        second_product = Product(
            sku="SKU-MULTI-002",
            name="Produto múltiplo 2",
            price=Decimal("7.50"),
            stock_quantity=6,
        )

        db.session.add_all([customer, first_product, second_product])
        db.session.commit()

        customer_id = customer.id
        first_product_id = first_product.id
        second_product_id = second_product.id

    response = client.post(
        "/sales",
        json={
            "customer_id": customer_id,
            "items": [
                {
                    "product_id": first_product_id,
                    "quantity": 3,
                },
                {
                    "product_id": second_product_id,
                    "quantity": 2,
                },
            ],
        },
    )

    assert response.status_code == 201

    sale_data = response.get_json()
    sale_id = sale_data["id"]

    confirm_response = client.post(
        f"/sales/{sale_id}/confirm"
    )

    assert confirm_response.status_code == 200

    data = confirm_response.get_json()

    assert data["customer_id"] == customer_id
    assert data["status"] == "CONFIRMED"
    assert data["total_amount"] == "45.00"
    assert len(data["items"]) == 2

    items_by_product = {
        item["product_id"]: item
        for item in data["items"]
    }

    assert items_by_product[first_product_id]["quantity"] == 3
    assert items_by_product[first_product_id]["unit_price"] == "10.00"
    assert items_by_product[second_product_id]["quantity"] == 2
    assert items_by_product[second_product_id]["unit_price"] == "7.50"

    with app.app_context():
        first_product = db.session.get(Product, first_product_id)
        second_product = db.session.get(Product, second_product_id)
        sale = db.session.get(Sale, data["id"])

        assert first_product.stock_quantity == 5
        assert second_product.stock_quantity == 4
        assert sale is not None
        assert sale.total_amount == Decimal("45.00")
        assert len(sale.items) == 2

def test_get_sale_returns_items_and_totals(client, app):
    with app.app_context():
        customer = Customer(
            document="77777777777",
            name="Cliente consulta venda",
        )

        product = Product(
            sku="SKU-GET-SALE-001",
            name="Produto consulta venda",
            price=Decimal("12.50"),
            stock_quantity=10,
        )

        db.session.add_all([customer, product])
        db.session.commit()

        sale = Sale(
            customer_id=customer.id,
            status="OPEN",
            total_amount=Decimal("25.00"),
        )
        db.session.add(sale)

        sale.items.append(
            SaleItem(
                product_id=product.id,
                quantity=2,
                unit_price=product.price,
            )
        )
        db.session.add(sale)
        db.session.commit()

        sale_id = sale.id
        product_id = product.id
        customer_id = customer.id

    response = client.get(f"/sales/{sale_id}")

    assert response.status_code == 200

    data = response.get_json()

    assert data["id"] == sale_id
    assert data["customer_id"] == customer_id
    assert data["status"] == "OPEN"
    assert data["total_amount"] == "25.00"
    assert data["items"] == [
        {
            "product_id": product_id,
            "quantity": 2,
            "unit_price": "12.50",
            "subtotal": "25.00",
        }
    ]

def test_failed_sale_creation_does_not_persist_sale(client, app):
    with app.app_context():
        customer = Customer(
            document="99999999999",
            name="Cliente falha de venda",
        )
        db.session.add(customer)
        db.session.commit()

        customer_id = customer.id
        initial_sales_count = db.session.query(Sale).count()

    response = client.post(
        "/sales",
        json={
            "customer_id": customer_id,
            "items": [
                {
                    "product_id": 999999,
                    "quantity": 1,
                }
            ],
        },
    )

    assert response.status_code == 404

    with app.app_context():
        assert db.session.query(Sale).count() == initial_sales_count

def test_failed_multi_item_sale_does_not_change_stock_or_persist_sale(client, app):
    with app.app_context():
        customer = Customer(
            document="11111111111",
            name="Cliente rollback múltiplo",
        )

        first_product = Product(
            sku="SKU-ROLLBACK-001",
            name="Produto rollback 1",
            price=Decimal("10.00"),
            stock_quantity=5,
        )

        second_product = Product(
            sku="SKU-ROLLBACK-002",
            name="Produto rollback 2",
            price=Decimal("20.00"),
            stock_quantity=1,
        )

        db.session.add_all([customer, first_product, second_product])
        db.session.commit()

        customer_id = customer.id
        first_product_id = first_product.id
        second_product_id = second_product.id
        initial_sales_count = db.session.query(Sale).count()

    response = client.post(
        "/sales",
        json={
            "customer_id": customer_id,
            "items": [
                {
                    "product_id": first_product_id,
                    "quantity": 2,
                },
                {
                    "product_id": second_product_id,
                    "quantity": 2,
                },
            ],
        },
    )

    assert response.status_code == 400

    with app.app_context():
        first_product = db.session.get(Product, first_product_id)
        second_product = db.session.get(Product, second_product_id)

        assert first_product.stock_quantity == 5
        assert second_product.stock_quantity == 1
        assert db.session.query(Sale).count() == initial_sales_count

def test_create_sale_rejects_duplicate_product_items(client, app):
    with app.app_context():
        customer = Customer(
            document="22222222222",
            name="Cliente produto duplicado",
        )
        product = Product(
            sku="SKU-DUPLICADO-001",
            name="Produto duplicado",
            price=Decimal("10.00"),
            stock_quantity=10,
        )

        db.session.add_all([customer, product])
        db.session.commit()

        customer_id = customer.id
        product_id = product.id
        initial_sales_count = db.session.query(Sale).count()

    response = client.post(
        "/sales",
        json={
            "customer_id": customer_id,
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 1,
                },
                {
                    "product_id": product_id,
                    "quantity": 2,
                },
            ],
        },
    )

    assert response.status_code == 400

    with app.app_context():
        product = db.session.get(Product, product_id)

        assert product.stock_quantity == 10
        assert db.session.query(Sale).count() == initial_sales_count

def test_invalid_item_after_valid_item_does_not_persist_sale(client, app):
    with app.app_context():
        customer = Customer(
            document="33333333333",
            name="Cliente validação completa",
        )
        product = Product(
            sku="SKU-VALIDACAO-001",
            name="Produto validação",
            price=Decimal("15.00"),
            stock_quantity=10,
        )

        db.session.add_all([customer, product])
        db.session.commit()

        customer_id = customer.id
        product_id = product.id
        initial_sales_count = db.session.query(Sale).count()

    response = client.post(
        "/sales",
        json={
            "customer_id": customer_id,
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 2,
                },
                {
                    "product_id": product_id + 999999,
                    "quantity": 1,
                },
            ],
        },
    )

    assert response.status_code == 404

    with app.app_context():
        product = db.session.get(Product, product_id)

        assert product.stock_quantity == 10
        assert db.session.query(Sale).count() == initial_sales_count

def test_list_sales_rejects_unknown_status(client):
    response = client.get("/sales?status=INVALID")

    assert response.status_code == 400
    assert response.get_json()["error"] == "invalid sale status"

def test_list_sales_rejects_zero_customer_id(client):
    response = client.get("/sales?customer_id=0")

    assert response.status_code == 400
    assert response.get_json()["error"] == "customer_id must be positive"


def test_list_sales_rejects_negative_customer_id(client):
    response = client.get("/sales?customer_id=-1")

    assert response.status_code == 400
    assert response.get_json()["error"] == "customer_id must be positive"


def test_list_sales_filters_by_status_and_customer(client, app):
    with app.app_context():
        customer_id, product_id = create_sale_data()

    response = client.post(
        "/sales",
        json={
            "customer_id": customer_id,
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 1,
                }
            ],
        },
    )

    assert response.status_code == 201
    sale_id = response.get_json()["id"]

    confirmed_response = client.post(f"/sales/{sale_id}/confirm")
    assert confirmed_response.status_code == 200

    response = client.get(
        f"/sales?status=CONFIRMED&customer_id={customer_id}"
    )

    assert response.status_code == 200
    data = response.get_json()

    assert len(data) == 1
    assert data[0]["id"] == sale_id
    assert data[0]["customer_id"] == customer_id
    assert data[0]["status"] == "CONFIRMED"

def test_list_sales_returns_empty_for_unknown_customer(client):
    response = client.get("/sales?customer_id=999999")

    assert response.status_code == 200
    assert response.get_json() == []

def test_list_sales_accepts_valid_status_values(client):
    for status in ("OPEN", "CONFIRMED", "CANCELLED"):
        response = client.get(f"/sales?status={status}")

        assert response.status_code == 200
        assert isinstance(response.get_json(), list)

def test_list_sales_paginated_returns_metadata(client):
    response = client.get("/sales/paginated")

    assert response.status_code == 200

    data = response.get_json()

    assert data["page"] == 1
    assert data["per_page"] == 10
    assert data["total"] == 0
    assert data["pages"] == 0
    assert data["items"] == []


def test_list_sales_paginated_rejects_invalid_page(client):
    response = client.get("/sales/paginated?page=0")

    assert response.status_code == 400
    assert response.get_json()["error"] == "page must be positive"


def test_list_sales_paginated_rejects_invalid_per_page(client):
    response = client.get("/sales/paginated?per_page=101")

    assert response.status_code == 400
    assert response.get_json()["error"] == (
        "per_page cannot be greater than 100"
    )

def test_list_sales_paginated_splits_results(client, app):
    with app.app_context():
        customer_id, product_id = create_sale_data()

    sale_ids = []

    for _ in range(3):
        response = client.post(
            "/sales",
            json={
                "customer_id": customer_id,
                "items": [
                    {
                        "product_id": product_id,
                        "quantity": 1,
                    }
                ],
            },
        )

        assert response.status_code == 201
        sale_ids.append(response.get_json()["id"])

    response = client.get("/sales/paginated?page=2&per_page=2")

    assert response.status_code == 200

    data = response.get_json()

    assert data["page"] == 2
    assert data["per_page"] == 2
    assert data["total"] == 3
    assert data["pages"] == 2
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == sale_ids[2]