from decimal import Decimal

from app import db
from app.purchase_models import Purchase
from app.supplier_models import Supplier


def test_list_purchases_supports_pagination(client, app):
    with app.app_context():
        supplier = Supplier(
            document="11222333000181",
            name="Fornecedor Paginação",
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

    first_page = client.get(
        "/purchases?page=1&per_page=2"
    )

    second_page = client.get(
        "/purchases?page=2&per_page=2"
    )

    assert first_page.status_code == 200
    assert second_page.status_code == 200

    first_body = first_page.get_json()
    second_body = second_page.get_json()

    first_items = first_body["items"]
    second_items = second_body["items"]

    assert len(first_items) == 2
    assert len(second_items) == 2

    assert first_body["page"] == 1
    assert second_body["page"] == 2
    assert first_body["per_page"] == 2
    assert second_body["per_page"] == 2
    assert first_body["total"] == 5
    assert first_body["pages"] == 3

    assert first_items[0]["id"] < second_items[0]["id"]


def test_list_purchases_rejects_invalid_page(client):
    response = client.get("/purchases?page=0")

    assert response.status_code == 400
    assert response.get_json()["error"] == (
        "page must be greater than zero"
    )


def test_list_purchases_rejects_invalid_per_page(client):
    response = client.get("/purchases?per_page=101")

    assert response.status_code == 400
    assert response.get_json()["error"] == (
        "per_page must be between 1 and 100"
    )