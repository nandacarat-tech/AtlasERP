from app import db
from app.stock_movement_models import StockMovement


class StockMovementError(Exception):
    """Erro de negócio relacionado a movimentações de estoque."""


def apply_stock_out(*, product, quantity, sale_id=None):
    if quantity <= 0:
        raise StockMovementError(
            "quantity must be greater than zero"
        )

    if product.stock_quantity < quantity:
        raise StockMovementError(
            "insufficient stock"
        )

    stock_before = product.stock_quantity
    product.stock_quantity -= quantity

    movement = StockMovement(
        product_id=product.id,
        sale_id=sale_id,
        movement_type="OUT",
        quantity=quantity,
        stock_before=stock_before,
        stock_after=product.stock_quantity,
    )

    db.session.add(movement)
    return movement