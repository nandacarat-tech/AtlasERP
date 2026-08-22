from decimal import Decimal

from app import create_app, db
from app.config import TestingConfig
from app.models import Product


def test_create_product():
    app = create_app(TestingConfig)

    with app.app_context():
        db.create_all()

        product = Product(
            sku="SKU-001",
            name="Produto de teste",
            price=Decimal("19.90"),
            stock_quantity=10,
        )

        db.session.add(product)
        db.session.commit()

        saved_product = Product.query.filter_by(
            sku="SKU-001"
        ).first()

        assert saved_product is not None
        assert saved_product.name == "Produto de teste"
        assert saved_product.price == Decimal("19.90")
        assert saved_product.stock_quantity == 10

        db.session.remove()
        db.drop_all()