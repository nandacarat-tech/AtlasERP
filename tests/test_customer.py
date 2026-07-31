from app import create_app, db
from app.config import TestingConfig
from app.customer_models import Customer


def test_create_customer():
    app = create_app(TestingConfig)

    with app.app_context():
        db.create_all()

        customer = Customer(
            document="12345678900",
            name="Cliente de teste",
            email="cliente@example.com",
            phone="11999999999",
        )

        db.session.add(customer)
        db.session.commit()

        saved_customer = Customer.query.filter_by(
            document="12345678900"
        ).first()

        assert saved_customer is not None
        assert saved_customer.name == "Cliente de teste"
        assert saved_customer.email == "cliente@example.com"
        assert saved_customer.is_active is True
