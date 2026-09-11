from decimal import Decimal

from app import create_app, db
from app.config import TestingConfig
from app.customer_models import Customer
from app.models import Product
from app.sale_models import Sale, SaleItem


def test_sale_calculates_total():
    app = create_app(TestingConfig)

    with app.app_context():
        db.create_all()

        customer = Customer(
            document="52998224725",
            name="Cliente da venda",
        )

        product = Product(
            sku="SKU-SALE-001",
            name="Produto vendido",
            price=Decimal("25.00"),
            stock_quantity=10,
        )

        db.session.add_all([customer, product])
        db.session.commit()

        sale = Sale(customer=customer)

        sale.items.append(SaleItem(
            product=product,
            quantity=2,
            unit_price=Decimal("25.00"),
        ))

        sale.items.append(SaleItem(
            product=product,
            quantity=1,
            unit_price=Decimal("10.00"),
        ))

        sale.recalculate_total()
        db.session.add(sale)
        db.session.commit()

        saved_sale = db.session.get(Sale, sale.id)

        assert saved_sale.total_amount == Decimal("60.00")
        assert len(saved_sale.items) == 2
        assert saved_sale.items[0].subtotal in (
            Decimal("50.00"),
            Decimal("10.00"),
        )
