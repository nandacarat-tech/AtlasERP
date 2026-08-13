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