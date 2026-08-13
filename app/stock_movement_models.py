from datetime import datetime, timezone

from sqlalchemy.orm import validates

from app import db


class StockMovement(db.Model):
    __tablename__ = "stock_movements"

    id = db.Column(db.Integer, primary_key=True)

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False,
    )

    sale_id = db.Column(
        db.Integer,
        db.ForeignKey("sales.id"),
        nullable=True,
    )

    purchase_id = db.Column(
        db.Integer,
        db.ForeignKey("purchases.id"),
        nullable=True,
    )

    movement_type = db.Column(
        db.String(10),
        nullable=False,
    )

    quantity = db.Column(
        db.Integer,
        nullable=False,
    )

    stock_before = db.Column(
        db.Integer,
        nullable=False,
    )

    stock_after = db.Column(
        db.Integer,
        nullable=False,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    @validates("movement_type")
    def validate_movement_type(self, key, value):
        if value not in {"IN", "OUT"}:
            raise ValueError(
                "movement_type must be IN or OUT"
            )

        return value

    @validates("quantity")
    def validate_quantity(self, key, value):
        if value <= 0:
            raise ValueError(
                "quantity must be greater than zero"
            )

        return value

    @validates("stock_before", "stock_after")
    def validate_stock_values(self, key, value):
        if value < 0:
            raise ValueError(
                f"{key} cannot be negative"
            )

        return value

    product = db.relationship(
        "Product",
        backref="stock_movements",
    )

    sale = db.relationship(
        "Sale",
        backref="stock_movements",
    )

    purchase = db.relationship(
        "Purchase",
        backref="stock_movements",
    )