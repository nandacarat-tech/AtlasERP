def test_list_purchases_rejects_invalid_status(client):
    response = client.get(
        "/purchases?status=UNKNOWN"
    )

    assert response.status_code == 400

    body = response.get_json()

    assert body["error"] == "invalid purchase status"
    assert body["allowed_statuses"] == [
        "CANCELED",
        "OPEN",
        "RECEIVED",
    ]


def test_list_purchases_accepts_canceled_status(client):
    response = client.get(
        "/purchases?status=CANCELED"
    )

    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


import pytest


@pytest.mark.parametrize(
    "value",
    ["abc", "0", "-1"],
)
def test_list_purchases_rejects_invalid_supplier_id(
    client,
    value,
):
    response = client.get(
        f"/purchases?supplier_id={value}"
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "supplier_id must be a positive integer"
    }