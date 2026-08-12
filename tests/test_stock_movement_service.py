from decimal import Decimal

import pytest

from app import db
from app.models import Product
from app.stock_movement_models import StockMovement
from app.stock_movement_service import (
    StockMovementError,
    apply_stock_out,
)


def create_product(stock_quantity=10):
    product = Product(
        sku=f"SKU-SERVICE-{stock_quantity}",
        name="Produto do serviço",
        price=Decimal("15.00"),
        stock_quantity=stock_quantity,
    )

    db.session.add(product)
    db.session.commit()

    return product


def test_apply_stock_out_reduces_stock_and_creates_movement(app):
    with app.app_context():
        product = create_product(stock_quantity=10)

        movement = apply_stock_out(
            product=product,
            quantity=2,
            sale_id=None,
        )

        db.session.commit()

        assert product.stock_quantity == 8
        assert movement.movement_type == "OUT"
        assert movement.quantity == 2
        assert movement.stock_before == 10
        assert movement.stock_after == 8

        saved_movement = db.session.get(
            StockMovement,
            movement.id,
        )

        assert saved_movement is not None
        assert saved_movement.product_id == product.id


def test_apply_stock_out_rejects_insufficient_stock(app):
    with app.app_context():
        product = create_product(stock_quantity=10)

        with pytest.raises(
            StockMovementError,
            match="insufficient stock",
        ):
            apply_stock_out(
                product=product,
                quantity=11,
            )

        assert product.stock_quantity == 10
        assert StockMovement.query.count() == 0


@pytest.mark.parametrize("quantity", [0, -1])
def test_apply_stock_out_rejects_non_positive_quantity(
    app,
    quantity,
):
    with app.app_context():
        product = create_product(stock_quantity=10)

        with pytest.raises(
            StockMovementError,
            match="quantity must be greater than zero",
        ):
            apply_stock_out(
                product=product,
                quantity=quantity,
            )

        assert product.stock_quantity == 10
        assert StockMovement.query.count() == 0
