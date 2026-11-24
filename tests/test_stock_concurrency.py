import pytest
from decimal import Decimal
from app import db
from app.models import Product
from app.stock_movement_service import apply_stock_out, StockMovementError


def test_atomic_stock_decrement_prevents_negative_inventory(app):
    """
    Comprova que a operação atômica impede que o estoque fique negativo
    mesmo sob requisições consecutivas no limite de disponibilidade.
    """
    with app.app_context():
        product = Product(
            sku="SKU-ATOMIC-01",
            name="Produto Teste Atômico",
            price=Decimal("150.00"),
            stock_quantity=5,
            minimum_stock=1,
        )
        db.session.add(product)
        db.session.commit()

        # 1. Primeira baixa consome todo o saldo (5 unidades)
        mov1 = apply_stock_out(product=product, quantity=5)
        db.session.commit()

        assert mov1.stock_before == 5
        assert mov1.stock_after == 0
        assert product.stock_quantity == 0

        # 2. Segunda baixa tenta consumir mais 1 unidade -> Deve falhar imediatamente
        with pytest.raises(StockMovementError) as exc_info:
            apply_stock_out(product=product, quantity=1)

        assert "insufficient stock" in str(exc_info.value)
        # Saldo permanece rigorosamente 0 (nunca negativo)
        assert product.stock_quantity == 0


def test_atomic_stock_multiple_partial_decrements(app):
    """
    Comprova a consistência matemática do saldo através de múltiplas baixas parciais.
    """
    with app.app_context():
        product = Product(
            sku="SKU-ATOMIC-02",
            name="Produto Baixas Parciais",
            price=Decimal("50.00"),
            stock_quantity=10,
        )
        db.session.add(product)
        db.session.commit()

        apply_stock_out(product=product, quantity=3)
        db.session.commit()
        assert product.stock_quantity == 7

        apply_stock_out(product=product, quantity=4)
        db.session.commit()
        assert product.stock_quantity == 3

        # Tentar baixar 4 quando só há 3
        with pytest.raises(StockMovementError):
            apply_stock_out(product=product, quantity=4)

        assert product.stock_quantity == 3
