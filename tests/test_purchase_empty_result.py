from decimal import Decimal

from app import db
from app.purchase_models import Purchase
from app.supplier_models import Supplier


def test_list_purchases_with_no_matching_results_returns_empty_list(
    client,
):
    response = client.get(
        "/purchases?status=OPEN&supplier_id=999999"
    )

    assert response.status_code == 200

    body = response.get_json()

    assert body == []