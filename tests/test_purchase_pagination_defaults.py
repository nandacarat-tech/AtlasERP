def test_list_purchases_uses_default_per_page(
    client,
):
    response = client.get(
        "/purchases?page=1"
    )

    assert response.status_code == 200

    body = response.get_json()

    assert body["page"] == 1
    assert body["per_page"] == 20
    assert "items" in body
    assert "total" in body
    assert "pages" in body

def test_list_purchases_without_pagination_returns_list(
    client,
):
    response = client.get(
        "/purchases"
    )

    assert response.status_code == 200

    body = response.get_json()

    assert isinstance(body, list)