import pytest


@pytest.mark.parametrize(
    "query_string",
    [
        "page=0",
        "page=-1",
        "per_page=0",
        "per_page=101",
    ],
)
def test_list_purchases_rejects_invalid_pagination(
    client,
    query_string,
):
    response = client.get(
        f"/purchases?{query_string}"
    )

    assert response.status_code == 400

    body = response.get_json()

    assert "error" in body