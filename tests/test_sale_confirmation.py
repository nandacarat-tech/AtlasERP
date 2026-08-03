from decimal import Decimal

from app import db
from app.customer_models import Customer
from app.models import Product
from app.sale_models import Sale, SaleItem


def create_open_sale():
    customer = Customer(
        document="55555555555",
        name="Cliente confirmação",
    )

    product = Product(
        sku="SKU-CONFIRM-001",
        name="Produto confirmação",
        price=Decimal("30.00"),
        stock_quantity=10,
    )

    db.session.add_all([customer, product])
    db.session.commit()

    sale = Sale(
        customer=customer,
        status="OPEN",
        total_amount=Decimal("60.00"),
    )
    db.session.add(sale)

    sale.items.append(SaleItem(
        product=product,
        quantity=2,
        unit_price=product.price,
    ))

    db.session.commit()

    return sale.id, product.id


def test_confirm_sale_decreases_stock(client, app):
    with app.app_context():
        sale_id, product_id = create_open_sale()

    response = client.post(f"/sales/{sale_id}/confirm")

    assert response.status_code == 200
    assert response.get_json()["status"] == "CONFIRMED"

    with app.app_context():
        product = db.session.get(Product, product_id)
        sale = db.session.get(Sale, sale_id)

        assert product.stock_quantity == 8
        assert sale.status == "CONFIRMED"


def test_confirm_sale_cannot_be_confirmed_twice(client, app):
    with app.app_context():
        sale_id, product_id = create_open_sale()

    first_response = client.post(f"/sales/{sale_id}/confirm")
    second_response = client.post(f"/sales/{sale_id}/confirm")

    assert first_response.status_code == 200
    assert second_response.status_code == 400
    assert "only open sales" in second_response.get_json()["error"]

    with app.app_context():
        product = db.session.get(Product, product_id)
        sale = db.session.get(Sale, sale_id)

        assert product.stock_quantity == 8
        assert sale.status == "CONFIRMED"



def test_confirm_sale_rejects_insufficient_stock(client, app):
    with app.app_context():
        customer = Customer(
            document="66666666666",
            name="Cliente estoque insuficiente",
        )

        product = Product(
            sku="SKU-CONFIRM-002",
            name="Produto sem estoque",
            price=Decimal("10.00"),
            stock_quantity=1,
        )

        db.session.add_all([customer, product])
        db.session.commit()

        sale = Sale(
            customer=customer,
            status="OPEN",
            total_amount=Decimal("20.00"),
        )

        db.session.add(sale)

        sale.items.append(SaleItem(
            product=product,
            quantity=2,
            unit_price=product.price,
        ))

        db.session.commit()
        sale_id = sale.id
        product_id = product.id

    response = client.post(f"/sales/{sale_id}/confirm")

    assert response.status_code == 400
    assert "insufficient stock" in response.get_json()["error"]

    with app.app_context():
        product = db.session.get(Product, product_id)
        sale = db.session.get(Sale, sale_id)

        assert product.stock_quantity == 1
        assert sale.status == "OPEN"
def test_cancel_open_sale(client, app):
    customer_response = client.post(
        "/customers",
        json={
            "name": "Cliente Cancelamento",
            "document": "99999999999",
        },
    )
    customer_id = customer_response.get_json()["id"]

    product_response = client.post(
        "/products",
        json={
            "sku": "CANCEL-001",
            "name": "Produto Cancelamento",
            "price": 25.0,
            "stock_quantity": 10,
        },
    )
    product_id = product_response.get_json()["id"]

    sale_response = client.post(
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
    sale_id = sale_response.get_json()["id"]

    response = client.post(f"/sales/{sale_id}/cancel")

    assert response.status_code == 200
    assert response.get_json()["status"] == "CANCELLED"

    with app.app_context():
        product = db.session.get(Product, product_id)
        assert product.stock_quantity == 10

def test_cancel_confirmed_sale_is_rejected(client, app):
    with app.app_context():
        sale_id, product_id = create_open_sale()

    confirm_response = client.post(f"/sales/{sale_id}/confirm")
    cancel_response = client.post(f"/sales/{sale_id}/cancel")

    assert confirm_response.status_code == 200
    assert cancel_response.status_code == 400
    assert "only open sales" in cancel_response.get_json()["error"]

    with app.app_context():
        product = db.session.get(Product, product_id)
        sale = db.session.get(Sale, sale_id)

        assert product.stock_quantity == 8
        assert sale.status == "CONFIRMED"

def test_cancel_nonexistent_sale_returns_not_found(client):
    response = client.post("/sales/999999/cancel")

    assert response.status_code == 404
    assert response.get_json()["error"] == "sale not found"

def test_cancel_sale_cannot_be_cancelled_twice(client, app):
    with app.app_context():
        sale_id, product_id = create_open_sale()

    first_response = client.post(f"/sales/{sale_id}/cancel")
    second_response = client.post(f"/sales/{sale_id}/cancel")

    assert first_response.status_code == 200
    assert second_response.status_code == 400
    assert "only open sales" in second_response.get_json()["error"]

    with app.app_context():
        product = db.session.get(Product, product_id)
        sale = db.session.get(Sale, sale_id)

        assert product.stock_quantity == 10
        assert sale.status == "CANCELLED"

def test_cancel_empty_sale_is_allowed_without_stock_change(client, app):
    with app.app_context():
        customer = Customer(
            document="88888888888",
            name="Cliente venda vazia",
        )
        db.session.add(customer)
        db.session.commit()

        sale = Sale(
            customer_id=customer.id,
            status="OPEN",
            total_amount=Decimal("0.00"),
        )
        db.session.add(sale)
        db.session.commit()

        sale_id = sale.id

    response = client.post(f"/sales/{sale_id}/cancel")

    assert response.status_code == 200
    assert response.get_json()["status"] == "CANCELLED"

    with app.app_context():
        sale = db.session.get(Sale, sale_id)
        assert sale.status == "CANCELLED"

def test_confirm_cancelled_sale_is_rejected(client, app):
    with app.app_context():
        sale_id, product_id = create_open_sale()

    cancel_response = client.post(f"/sales/{sale_id}/cancel")
    confirm_response = client.post(f"/sales/{sale_id}/confirm")

    assert cancel_response.status_code == 200
    assert confirm_response.status_code == 400
    assert "open sales" in confirm_response.get_json()["error"].lower()

    with app.app_context():
        product = db.session.get(Product, product_id)
        sale = db.session.get(Sale, sale_id)

        assert product.stock_quantity == 10
        assert sale.status == "CANCELLED"

def test_confirm_sale_cannot_be_confirmed_twice(client, app):
    with app.app_context():
        sale_id, product_id = create_open_sale()

    first_response = client.post(f"/sales/{sale_id}/confirm")
    second_response = client.post(f"/sales/{sale_id}/confirm")

    assert first_response.status_code == 200
    assert second_response.status_code == 400
    assert "open sales" in second_response.get_json()["error"].lower()

    with app.app_context():
        product = db.session.get(Product, product_id)
        sale = db.session.get(Sale, sale_id)

        assert product.stock_quantity == 8
        assert sale.status == "CONFIRMED"


def test_confirm_sale_does_not_allow_stock_to_become_negative(client, app):
    with app.app_context():
        customer = Customer(
            document="99999999999",
            name="Cliente concorrência",
        )
        product = Product(
            sku="SKU-CONCURRENCY-001",
            name="Produto concorrência",
            price=Decimal("10.00"),
            stock_quantity=1,
        )

        db.session.add_all([customer, product])
        db.session.commit()

        sale = Sale(
            customer_id=customer.id,
            status="OPEN",
            total_amount=Decimal("10.00"),
        )
        sale.items.append(
            SaleItem(
                product=product,
                quantity=1,
                unit_price=product.price,
            )
        )

        db.session.add(sale)
        db.session.commit()

        product_id = product.id
        sale_id = sale.id

    response = client.post(f"/sales/{sale_id}/confirm")

    assert response.status_code == 200

    with app.app_context():
        product = db.session.get(Product, product_id)

        assert product.stock_quantity == 0
        assert product.stock_quantity >= 0


def test_confirm_multi_item_sale_rolls_back_stock_on_failure(client, app):
    with app.app_context():
        customer = Customer(
            document="88888888888",
            name="Cliente rollback confirmação",
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

        sale = Sale(
            customer_id=customer.id,
            status="OPEN",
            total_amount=Decimal("50.00"),
        )
        sale.items.extend(
            [
                SaleItem(
                    product=first_product,
                    quantity=2,
                    unit_price=first_product.price,
                ),
                SaleItem(
                    product=second_product,
                    quantity=2,
                    unit_price=second_product.price,
                ),
            ]
        )

        db.session.add(sale)
        db.session.commit()

        sale_id = sale.id
        first_product_id = first_product.id
        second_product_id = second_product.id

    response = client.post(f"/sales/{sale_id}/confirm")

    assert response.status_code == 400
    assert "insufficient stock" in response.get_json()["error"]

    with app.app_context():
        saved_sale = db.session.get(Sale, sale_id)
        saved_first_product = db.session.get(Product, first_product_id)
        saved_second_product = db.session.get(Product, second_product_id)

        assert saved_sale.status == "OPEN"
        assert saved_first_product.stock_quantity == 5
        assert saved_second_product.stock_quantity == 1