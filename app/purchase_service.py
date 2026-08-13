from datetime import datetime, timezone

from app import db
from app.purchase_status import OPEN, RECEIVED
from app.stock_movement_service import apply_stock_in


class PurchaseError(Exception):
    """Purchase business error."""


def receive_purchase(*, purchase):
    if purchase.status != OPEN:
        raise PurchaseError(
            "purchase cannot be received in its current status"
        )

    if purchase.supplier is None:
        raise PurchaseError("supplier not found")

    if not purchase.supplier.is_active:
        raise PurchaseError("supplier is inactive")

    if not purchase.items:
        raise PurchaseError("purchase must have at least one item")

    for item in purchase.items:
        if item.quantity <= 0:
            raise PurchaseError(
                "item quantity must be greater than zero"
            )

        if item.unit_cost <= 0:
            raise PurchaseError(
                "item unit_cost must be greater than zero"
            )

        if item.product is None:
            raise PurchaseError("product not found")

        if not item.product.is_active:
            raise PurchaseError("product is inactive")

    for item in purchase.items:
        apply_stock_in(
            product=item.product,
            quantity=item.quantity,
            purchase_id=purchase.id,
        )

    purchase.recalculate_total()
    purchase.status = RECEIVED
    purchase.received_at = datetime.now(timezone.utc)

    return purchase
