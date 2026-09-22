from app import create_app


def test_index():
    app = create_app()
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 302
    assert response.location == "/dashboard"

