from decimal import Decimal

from app import db
from app.purchase_models import Purchase
from app.supplier_models import Supplier


def test_paginated_purchase_response_contains_metadata(client, app):
    with app.app_context():
        supplier = Supplier(
            document="11222333000181",
            name="Fornecedor Metadados",
            is_active=True,
        )

        db.session.add(supplier)
        db.session.flush()

        for _ in range(5):
            db.session.add(
                Purchase(
                    supplier_id=supplier.id,
                    status="OPEN",
                    total_amount=Decimal("0.00"),
                )
            )

        db.session.commit()

    response = client.get(
        "/purchases?page=2&per_page=2"
    )

    assert response.status_code == 200

    body = response.get_json()

    assert body["page"] == 2
    assert body["per_page"] == 2
    assert body["total"] == 5
    assert body["pages"] == 3
    assert len(body["items"]) == 2


def test_paginated_purchase_response_supports_filters(
    client,
    app,
):
    with app.app_context():
        supplier_a = Supplier(
            document="00000000000191",
            name="Fornecedor Metadados A",
            is_active=True,
        )

        supplier_b = Supplier(
            document="12345678000195",
            name="Fornecedor Metadados B",
            is_active=True,
        )

        db.session.add_all([supplier_a, supplier_b])
        db.session.flush()

        for _ in range(3):
            db.session.add(
                Purchase(
                    supplier_id=supplier_a.id,
                    status="OPEN",
                    total_amount=Decimal("0.00"),
                )
            )

        db.session.add(
            Purchase(
                supplier_id=supplier_a.id,
                status="RECEIVED",
                total_amount=Decimal("0.00"),
            )
        )

        db.session.add(
            Purchase(
                supplier_id=supplier_b.id,
                status="OPEN",
                total_amount=Decimal("0.00"),
            )
        )

        supplier_id = supplier_a.id
        db.session.commit()

    response = client.get(
        "/purchases"
        f"?status=OPEN&supplier_id={supplier_id}"
        "&page=1&per_page=2"
    )

    assert response.status_code == 200

    body = response.get_json()

    assert body["total"] == 3
    assert body["pages"] == 2
    assert len(body["items"]) == 2
    assert all(
        item["status"] == "OPEN"
        for item in body["items"]
    )
    assert all(
        item["supplier_id"] == supplier_id
        for item in body["items"]
    )


def test_unpaginated_purchase_response_remains_a_list(client):
    response = client.get("/purchases")

    assert response.status_code == 200
    assert isinstance(response.get_json(), list)

def test_list_purchases_pagination_metadata_is_consistent(
    client,
):
    response = client.get(
        "/purchases?page=1&per_page=2"
    )

    assert response.status_code == 200

    body = response.get_json()

    assert body["page"] == 1
    assert body["per_page"] == 2
    assert body["total"] >= len(body["items"])

    expected_pages = (
        (body["total"] + body["per_page"] - 1)
        // body["per_page"]
    )

    assert body["pages"] == expected_pages