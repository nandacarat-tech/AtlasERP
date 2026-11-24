from app import db
from app.stock_movement_models import StockMovement
from app.models import Product


class StockMovementError(Exception):
    """Erro de negócio relacionado a movimentações de estoque."""


def apply_stock_out(*, product, quantity, sale_id=None):
    if quantity <= 0:
        raise StockMovementError(
            "quantity must be greater than zero"
        )

    stock_before = product.stock_quantity

    # Operação atômica condicional no banco de dados (mitigação contra Race Conditions)
    # Impede saldo negativo mesmo sob requisições de vendas concorrentes simultâneas
    result = db.session.execute(
        db.update(Product)
        .where(Product.id == product.id, Product.stock_quantity >= quantity)
        .values(stock_quantity=Product.stock_quantity - quantity)
    )

    if result.rowcount == 0:
        db.session.refresh(product)
        raise StockMovementError(
            "insufficient stock"
        )

    db.session.refresh(product)
    stock_after = product.stock_quantity

    movement = StockMovement(
        product_id=product.id,
        sale_id=sale_id,
        movement_type="OUT",
        quantity=quantity,
        stock_before=stock_before,
        stock_after=stock_after,
    )

    db.session.add(movement)
    return movement


def apply_stock_in(*, product, quantity, purchase_id=None):
    if quantity <= 0:
        raise StockMovementError(
            "quantity must be greater than zero"
        )

    stock_before = product.stock_quantity

    db.session.execute(
        db.update(Product)
        .where(Product.id == product.id)
        .values(stock_quantity=Product.stock_quantity + quantity)
    )
    db.session.refresh(product)
    stock_after = product.stock_quantity

    movement = StockMovement(
        product_id=product.id,
        purchase_id=purchase_id,
        movement_type="IN",
        quantity=quantity,
        stock_before=stock_before,
        stock_after=stock_after,
    )

    db.session.add(movement)
    return movement