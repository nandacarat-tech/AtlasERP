from decimal import Decimal

from app import db
from app.purchase_models import Purchase
from app.supplier_models import Supplier


def create_supplier(document, name):
    supplier = Supplier(
        document=document,
        name=name,
        is_active=True,
    )

    db.session.add(supplier)
    db.session.flush()

    return supplier


def create_purchase(supplier_id, status):
    purchase = Purchase(
        supplier_id=supplier_id,
        status=status,
        total_amount=Decimal("0.00"),
    )

    db.session.add(purchase)
    db.session.flush()

    return purchase


def test_list_purchases_filters_by_status(client, app):
    with app.app_context():
        supplier = create_supplier(
            "FILTER-SUP-001",
            "Fornecedor Filtro Status",
        )

        create_purchase(supplier.id, "OPEN")
        create_purchase(supplier.id, "RECEIVED")
        create_purchase(supplier.id, "CANCELED")

        db.session.commit()

    response = client.get("/purchases?status=OPEN")

    assert response.status_code == 200

    purchases = response.get_json()

    assert len(purchases) == 1
    assert purchases[0]["status"] == "OPEN"


def test_list_purchases_filters_by_supplier(client, app):
    with app.app_context():
        supplier_a = create_supplier(
            "FILTER-SUP-002",
            "Fornecedor A",
        )

        supplier_b = create_supplier(
            "FILTER-SUP-003",
            "Fornecedor B",
        )

        create_purchase(supplier_a.id, "OPEN")
        create_purchase(supplier_a.id, "RECEIVED")
        create_purchase(supplier_b.id, "OPEN")

        supplier_id = supplier_a.id
        db.session.commit()

    response = client.get(
        f"/purchases?supplier_id={supplier_id}"
    )

    assert response.status_code == 200

    purchases = response.get_json()

    assert len(purchases) == 2
    assert all(
        purchase["supplier_id"] == supplier_id
        for purchase in purchases
    )


def test_list_purchases_filters_by_status_and_supplier(
    client,
    app,
):
    with app.app_context():
        supplier_a = create_supplier(
            "FILTER-SUP-004",
            "Fornecedor Combinado A",
        )

        supplier_b = create_supplier(
            "FILTER-SUP-005",
            "Fornecedor Combinado B",
        )

        create_purchase(supplier_a.id, "OPEN")
        create_purchase(supplier_a.id, "RECEIVED")
        create_purchase(supplier_b.id, "OPEN")

        supplier_id = supplier_a.id
        db.session.commit()

    response = client.get(
        f"/purchases?status=RECEIVED&supplier_id={supplier_id}"
    )

    assert response.status_code == 200

    purchases = response.get_json()

    assert len(purchases) == 1
    assert purchases[0]["status"] == "RECEIVED"
    assert purchases[0]["supplier_id"] == supplier_id


def test_list_purchases_invalid_supplier_id_returns_empty_list(
    client,
):
    response = client.get("/purchases?supplier_id=999999")

    assert response.status_code == 200
    assert response.get_json() == []