from app import db
from app.customer_models import Customer


def test_create_customer(client):
    response = client.post(
        "/customers",
        json={
            "document": "12345678900",
            "name": "Cliente novo",
            "email": "cliente@example.com",
            "phone": "11999999999",
        },
    )

    assert response.status_code == 201

    data = response.get_json()
    assert data["document"] == "12345678900"
    assert data["name"] == "Cliente novo"
    assert data["is_active"] is True


def test_list_customers(client, app):
    with app.app_context():
        db.session.add(Customer(
            document="98765432100",
            name="Cliente listado",
        ))
        db.session.commit()

    response = client.get("/customers")

    assert response.status_code == 200
    assert len(response.get_json()) == 1
    assert response.get_json()[0]["name"] == "Cliente listado"


def test_update_customer(client, app):
    with app.app_context():
        customer = Customer(
            document="11111111111",
            name="Nome antigo",
        )
        db.session.add(customer)
        db.session.commit()
        customer_id = customer.id

    response = client.put(
        f"/customers/{customer_id}",
        json={
            "name": "Nome atualizado",
            "phone": "11888888888",
        },
    )

    assert response.status_code == 200

    data = response.get_json()
    assert data["name"] == "Nome atualizado"
    assert data["phone"] == "11888888888"


def test_deactivate_customer(client, app):
    with app.app_context():
        customer = Customer(
            document="22222222222",
            name="Cliente ativo",
        )
        db.session.add(customer)
        db.session.commit()
        customer_id = customer.id

    response = client.delete(f"/customers/{customer_id}")

    assert response.status_code == 200
    assert response.get_json()["is_active"] is False


def test_create_customer_requires_document_and_name(client):
    response = client.post(
        "/customers",
        json={"email": "incompleto@example.com"},
    )

    assert response.status_code == 400

def test_update_customer_rejects_string_is_active(client, app):
    with app.app_context():
        customer = Customer(
            document="12345678901",
            name="Cliente Booleano",
            email="boolean@example.com",
            is_active=True,
        )
        db.session.add(customer)
        db.session.commit()
        customer_id = customer.id

    response = client.put(
        f"/customers/{customer_id}",
        json={"is_active": "false"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "is_active must be a boolean"