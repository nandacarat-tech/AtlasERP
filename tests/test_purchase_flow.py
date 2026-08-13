from decimal import Decimal

from app import db
from app.models import Product
from app.purchase_models import Purchase, PurchaseItem
from app.stock_movement_models import StockMovement
from app.supplier_models import Supplier


def test_purchase_full_flow(client, app):
    supplier_response = client.post(
        "/suppliers",
        json={
            "document": "SUP-0001",
            "name": "Fornecedor Teste",
            "email": "supplier.test@example.com",
        },
    )

    assert supplier_response.status_code == 201
    supplier = supplier_response.get_json()

    with app.app_context():
        product = Product(
            sku="PURCHASE-PRODUCT-001",
            name="Produto para Compra",
            price=Decimal("10.00"),
            stock_quantity=0,
            is_active=True,
        )

        db.session.add(product)
        db.session.commit()
        product_id = product.id

    purchase_response = client.post(
        "/purchases",
        json={"supplier_id": supplier["id"]},
    )

    assert purchase_response.status_code == 201
    purchase = purchase_response.get_json()

    item_response = client.post(
        f"/purchases/{purchase['id']}/items",
        json={
            "product_id": product_id,
            "quantity": 5,
            "unit_cost": 7.50,
        },
    )

    assert item_response.status_code == 201

    receive_response = client.post(
        f"/purchases/{purchase['id']}/receive"
    )

    assert receive_response.status_code == 200

    received = receive_response.get_json()

    assert received["status"] == "RECEIVED"
    assert received["total_amount"] == "37.50"

    with app.app_context():
        product = db.session.get(Product, product_id)

        assert product.stock_quantity == 5

        movement = StockMovement.query.filter_by(
            purchase_id=purchase["id"]
        ).one()

        assert movement.movement_type == "IN"
        assert movement.quantity == 5
        assert movement.stock_before == 0
        assert movement.stock_after == 5


def test_received_purchase_cannot_be_received_twice(client, app):
    with app.app_context():
        supplier = Supplier(
            document="SUP-0002",
            name="Outro Fornecedor",
            is_active=True,
        )

        product = Product(
            sku="PURCHASE-PRODUCT-002",
            name="Outro Produto",
            price=Decimal("12.00"),
            stock_quantity=2,
            is_active=True,
        )

        db.session.add_all([supplier, product])
        db.session.flush()

        purchase = Purchase(
            supplier_id=supplier.id,
            status="OPEN",
            total_amount=Decimal("0.00"),
        )

        item = PurchaseItem(
            purchase=purchase,
            product_id=product.id,
            quantity=3,
            unit_cost=Decimal("4.00"),
        )

        purchase.items.append(item)
        db.session.add(purchase)
        db.session.commit()

        purchase_id = purchase.id
        product_id = product.id

    first_response = client.post(
        f"/purchases/{purchase_id}/receive"
    )

    assert first_response.status_code == 200

    with app.app_context():
        product = db.session.get(Product, product_id)
        stock_after_first_receive = product.stock_quantity

    second_response = client.post(
        f"/purchases/{purchase_id}/receive"
    )

    assert second_response.status_code == 400

    with app.app_context():
        product = db.session.get(Product, product_id)

        assert product.stock_quantity == stock_after_first_receive

        movements = StockMovement.query.filter_by(
            purchase_id=purchase_id
        ).all()

        assert len(movements) == 1