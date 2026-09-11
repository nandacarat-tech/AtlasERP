from app import db
from app.supplier_models import Supplier


def test_create_supplier(client):
    response = client.post(
        "/suppliers",
        json={
            "document": "11222333000181",
            "name": "Fornecedor Novo",
            "email": "fornecedor@example.com",
            "phone": "1133334444",
        },
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["document"] == "11.222.333/0001-81"
    assert data["phone"] == "(11) 3333-4444"


def test_create_supplier_invalid_document_rejected(client):
    response = client.post(
        "/suppliers",
        json={
            "document": "11222333000100",
            "name": "CNPJ Invalido",
        },
    )
    assert response.status_code == 400
    assert "CNPJ inválido" in response.get_json()["error"]


def test_update_supplier_rejects_string_is_active(client, app):
    with app.app_context():
        supplier = Supplier(
            document="11222333000181",
            name="Fornecedor Booleano",
            email="supplier.boolean@example.com",
            is_active=True,
        )
        db.session.add(supplier)
        db.session.commit()
        supplier_id = supplier.id

    response = client.patch(
        f"/suppliers/{supplier_id}",
        json={"is_active": "false"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "is_active must be a boolean"