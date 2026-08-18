def test_list_purchases_returns_empty_items_for_page_out_of_range(
    client,
):
    response = client.get(
        "/purchases?page=999&per_page=20"
    )

    assert response.status_code == 200

    body = response.get_json()

    assert body["page"] == 999
    assert body["per_page"] == 20
    assert body["items"] == []
    assert "total" in body
    assert "pages" in body