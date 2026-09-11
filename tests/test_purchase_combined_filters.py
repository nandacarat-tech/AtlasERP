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
            document="11222333000181",
            name="Fornecedor Filtro Combinado A",
            is_active=True,
        )

        supplier_b = Supplier(
            document="00000000000191",
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
            document="12345678000195",
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

def test_list_purchases_combined_filters_with_pagination(
    client,
    app,
):
    with app.app_context():
        supplier = Supplier(
            document="60701190000104",
            name="Fornecedor Com Paginação",
            is_active=True,
        )

        db.session.add(supplier)
        db.session.flush()

        db.session.add_all(
            [
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
                Purchase(
                    supplier_id=supplier.id,
                    status="OPEN",
                    total_amount=Decimal("300.00"),
                ),
                Purchase(
                    supplier_id=supplier.id,
                    status="RECEIVED",
                    total_amount=Decimal("400.00"),
                ),
            ]
        )

        db.session.commit()

        supplier_id = supplier.id

    response = client.get(
        (
            "/purchases"
            f"?status=OPEN"
            f"&supplier_id={supplier_id}"
            "&page=1"
            "&per_page=2"
        )
    )

    assert response.status_code == 200

    body = response.get_json()

    assert body["page"] == 1
    assert body["per_page"] == 2
    assert body["total"] == 3
    assert body["pages"] == 2
    assert len(body["items"]) == 2

    for item in body["items"]:
        assert item["status"] == "OPEN"
        assert item["supplier_id"] == supplier_id

def test_list_purchases_combined_filters_second_page(
    client,
    app,
):
    with app.app_context():
        supplier = Supplier(
            document="33000167000101",
            name="Fornecedor Segunda Página",
            is_active=True,
        )

        db.session.add(supplier)
        db.session.flush()

        db.session.add_all(
            [
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
                Purchase(
                    supplier_id=supplier.id,
                    status="OPEN",
                    total_amount=Decimal("300.00"),
                ),
            ]
        )

        db.session.commit()

        supplier_id = supplier.id

    response = client.get(
        (
            "/purchases"
            f"?status=OPEN"
            f"&supplier_id={supplier_id}"
            "&page=2"
            "&per_page=2"
        )
    )

    assert response.status_code == 200

    body = response.get_json()

    assert body["page"] == 2
    assert body["per_page"] == 2
    assert body["total"] == 3
    assert body["pages"] == 2
    assert len(body["items"]) == 1
    assert body["items"][0]["status"] == "OPEN"
    assert body["items"][0]["supplier_id"] == supplier_id