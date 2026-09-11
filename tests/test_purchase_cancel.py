from decimal import Decimal

from app import db
from app.purchase_models import Purchase
from app.supplier_models import Supplier


def test_open_purchase_can_be_canceled(client, app):
    with app.app_context():
        supplier = Supplier(
            document="11222333000181",
            name="Fornecedor Cancelamento",
            is_active=True,
        )

        db.session.add(supplier)
        db.session.flush()

        purchase = Purchase(
            supplier_id=supplier.id,
            status="OPEN",
            total_amount=Decimal("0.00"),
        )

        db.session.add(purchase)
        db.session.commit()

        purchase_id = purchase.id

    response = client.post(
        f"/purchases/{purchase_id}/cancel"
    )

    assert response.status_code == 200
    assert response.get_json()["status"] == "CANCELED"


def test_received_purchase_cannot_be_canceled(client, app):
    with app.app_context():
        supplier = Supplier(
            document="00000000000191",
            name="Fornecedor Recebido",
            is_active=True,
        )

        db.session.add(supplier)
        db.session.flush()

        purchase = Purchase(
            supplier_id=supplier.id,
            status="RECEIVED",
            total_amount=Decimal("10.00"),
        )

        db.session.add(purchase)
        db.session.commit()

        purchase_id = purchase.id

    response = client.post(
        f"/purchases/{purchase_id}/cancel"
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == (
        "only open purchases can be canceled"
    )