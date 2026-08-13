from decimal import Decimal

from app import db
from app.purchase_models import Purchase
from app.supplier_models import Supplier


def test_list_purchases_combines_status_and_supplier_filters(
    client,
    app,
):
    with app.app_context():
        supplier_a = Supplier(
            document="COMBINED-SUP-001",
            name="Fornecedor Filtro Combinado A",
            is_active=True,
        )

        supplier_b = Supplier(
            document="COMBINED-SUP-002",
            name="Fornecedor Filtro Combinado B",
            is_active=True,
        )

        db.session.add_all([supplier_a, supplier_b])
        db.session.flush()

        db.session.add_all(
            [
                Purchase(
                    supplier_id=supplier_a.id,
                    status="OPEN",
                    total_amount=Decimal("100.00"),
                ),
                Purchase(
                    supplier_id=supplier_a.id,
                    status="RECEIVED",
                    total_amount=Decimal("200.00"),
                ),
                Purchase(
                    supplier_id=supplier_b.id,
                    status="OPEN",
                    total_amount=Decimal("300.00"),
                ),
            ]
        )

        db.session.commit()

        supplier_id = supplier_a.id

    response = client.get(
        f"/purchases?status=OPEN&supplier_id={supplier_id}"
    )

    assert response.status_code == 200

    items = response.get_json()

    assert len(items) == 1
    assert items[0]["status"] == "OPEN"
    assert items[0]["supplier_id"] == supplier_id

def test_list_purchases_combined_filters_can_return_empty_list(
    client,
    app,
):
    with app.app_context():
        supplier = Supplier(
            document="COMBINED-SUP-003",
            name="Fornecedor Sem Resultado",
            is_active=True,
        )

        db.session.add(supplier)
        db.session.flush()

        db.session.add(
            Purchase(
                supplier_id=supplier.id,
                status="RECEIVED",
                total_amount=Decimal("400.00"),
            )
        )

        db.session.commit()

        supplier_id = supplier.id

    response = client.get(
        f"/purchases?status=OPEN&supplier_id={supplier_id}"
    )

    assert response.status_code == 200
    assert response.get_json() == []

from decimal import Decimal

from app import db
from app.purchase_models import Purchase
from app.supplier_models import Supplier


def test_list_purchases_combines_status_and_supplier_filters(
    client,
    app,
):
    with app.app_context():
        supplier_a = Supplier(
            document="COMBINED-SUP-001",
            name="Fornecedor Filtro Combinado A",
            is_active=True,
        )

        supplier_b = Supplier(
            document="COMBINED-SUP-002",
            name="Fornecedor Filtro Combinado B",
            is_active=True,
        )

        db.session.add_all([supplier_a, supplier_b])
        db.session.flush()

        db.session.add_all(
            [
                Purchase(
                    supplier_id=supplier_a.id,
                    status="OPEN",
                    total_amount=Decimal("100.00"),
                ),
                Purchase(
                    supplier_id=supplier_a.id,
                    status="RECEIVED",
                    total_amount=Decimal("200.00"),
                ),
                Purchase(
                    supplier_id=supplier_b.id,
                    status="OPEN",
                    total_amount=Decimal("300.00"),
                ),
            ]
        )

        db.session.commit()

        supplier_id = supplier_a.id

    response = client.get(
        f"/purchases?status=OPEN&supplier_id={supplier_id}"
    )

    assert response.status_code == 200

    items = response.get_json()

    assert len(items) == 1
    assert items[0]["status"] == "OPEN"
    assert items[0]["supplier_id"] == supplier_id

def test_list_purchases_combined_filters_return_empty_list(
    client,
    app,
):
    with app.app_context():
        supplier = Supplier(
            document="COMBINED-SUP-003",
            name="Fornecedor Sem Resultado",
            is_active=True,
        )

        db.session.add(supplier)
        db.session.flush()

        db.session.add(
            Purchase(
                supplier_id=supplier.id,
                status="RECEIVED",
                total_amount=Decimal("400.00"),
            )
        )

        db.session.commit()

        supplier_id = supplier.id

    response = client.get(
        f"/purchases?status=OPEN&supplier_id={supplier_id}"
    )

    assert response.status_code == 200
    assert response.get_json() == []