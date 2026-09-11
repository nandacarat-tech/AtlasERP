from app import db
from app.customer_models import Customer


def test_create_customer(client):
    response = client.post(
        "/customers",
        json={
            "document": "52998224725",
            "name": "Cliente novo",
            "email": "cliente@example.com",
            "phone": "11999999999",
        },
    )

    assert response.status_code == 201

    data = response.get_json()
    assert data["document"] == "529.982.247-25"
    assert data["phone"] == "(11) 99999-9999"
    assert data["name"] == "Cliente novo"
    assert data["is_active"] is True


def test_list_customers(client, app):
    with app.app_context():
        db.session.add(Customer(
            document="11144477735",
            name="Cliente listado",
        ))
        db.session.commit()

    response = client.get("/customers")

    assert response.status_code == 200
    assert len(response.get_json()) == 1
    assert response.get_json()[0]["name"] == "Cliente listado"
    assert response.get_json()[0]["document"] == "111.444.777-35"


def test_update_customer(client, app):
    with app.app_context():
        customer = Customer(
            document="52998224725",
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
    assert data["phone"] == "(11) 88888-8888"


def test_deactivate_customer(client, app):
    with app.app_context():
        customer = Customer(
            document="11222333000181",
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


def test_create_customer_invalid_cpf_rejected(client):
    response = client.post(
        "/customers",
        json={
            "document": "12345678900",
            "name": "CPF Invalido",
        },
    )
    assert response.status_code == 400
    assert "CPF inválido" in response.get_json()["error"]


def test_create_customer_invalid_phone_rejected(client):
    response = client.post(
        "/customers",
        json={
            "document": "52998224725",
            "name": "Telefone Invalido",
            "phone": "1234",
        },
    )
    assert response.status_code == 400
    assert "Telefone inválido" in response.get_json()["error"]


def test_create_customer_valid_cnpj(client):
    response = client.post(
        "/customers",
        json={
            "document": "11.222.333/0001-81",
            "name": "Empresa LTDA",
            "phone": "(11) 3333-4444",
        },
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["document"] == "11.222.333/0001-81"
    assert data["phone"] == "(11) 3333-4444"


def test_update_customer_rejects_string_is_active(client, app):
    with app.app_context():
        customer = Customer(
            document="10000000019",
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