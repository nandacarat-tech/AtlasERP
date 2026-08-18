from decimal import Decimal

from app import db
from app.purchase_models import Purchase
from app.supplier_models import Supplier


def test_list_purchases_returns_items_ordered_by_id(
    client,
    app,
):
    with app.app_context():
        supplier = Supplier(
            document="ORDER-SUP-001",
            name="Fornecedor Ordenação",
            is_active=True,
        )

        db.session.add(supplier)
        db.session.flush()

        purchases = [
            Purchase(
                supplier_id=supplier.id,
                status="OPEN",
                total_amount=Decimal("300.00"),
            ),
            Purchase(
                supplier_id=supplier.id,
                status="OPEN",
                total_amount=Decimal("100.00"),
            ),
            Purchase(
                supplier_id=supplier.id,
                status="OPEN",
                total_amount=Decimal("200.00"),
            ),
        ]

        db.session.add_all(purchases)
        db.session.commit()

        expected_ids = sorted(purchase.id for purchase in purchases)

    response = client.get("/purchases")

    assert response.status_code == 200

    body = response.get_json()

    returned_ids = [item["id"] for item in body]

    assert returned_ids == expected_ids