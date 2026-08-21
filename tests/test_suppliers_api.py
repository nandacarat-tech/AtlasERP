from app import db
from app.supplier_models import Supplier


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