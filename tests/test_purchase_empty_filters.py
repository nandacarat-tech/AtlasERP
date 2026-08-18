def test_list_purchases_rejects_empty_filters(
    client,
):
    response = client.get(
        "/purchases?status=&supplier_id="
    )

    assert response.status_code == 400

    body = response.get_json()

    assert "error" in body