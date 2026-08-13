from decimal import Decimal

from app import db

from sqlalchemy.orm import validates

from app import db

class Purchase(db.Model):
    __tablename__ = "purchases"

    id = db.Column(db.Integer, primary_key=True)

    supplier_id = db.Column(
        db.Integer,
        db.ForeignKey("suppliers.id"),
        nullable=False,
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="OPEN",
    )

    total_amount = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    received_at = db.Column(
        db.DateTime,
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
    )

    supplier = db.relationship("Supplier", backref="purchases")

    items = db.relationship(
        "PurchaseItem",
        back_populates="purchase",
        cascade="all, delete-orphan",
    )

    def recalculate_total(self):
        self.total_amount = sum(
            (item.subtotal for item in self.items),
            Decimal("0.00"),
        )
    
    @validates("status")
    def validate_status(self, key, value):
        from app.purchase_status import PURCHASE_STATUSES

        if value not in PURCHASE_STATUSES:
            raise ValueError(f"Invalid purchase status: {value}")

        return value

class PurchaseItem(db.Model):
    __tablename__ = "purchase_items"

    id = db.Column(db.Integer, primary_key=True)

    purchase_id = db.Column(
        db.Integer,
        db.ForeignKey("purchases.id"),
        nullable=False,
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False,
    )

    quantity = db.Column(db.Integer, nullable=False)
    unit_cost = db.Column(db.Numeric(10, 2), nullable=False)

    purchase = db.relationship(
        "Purchase",
        back_populates="items",
    )

    product = db.relationship("Product")

    @property
    def subtotal(self):
        return self.unit_cost * self.quantity
   
    @validates("quantity")
    def validate_quantity(self, key, value):
        if value <= 0:
            raise ValueError(
                "quantity must be greater than zero"
            )
        return value

    @validates("unit_cost")
    def validate_unit_cost(self, key, value):
        if value <= 0:
            raise ValueError(
                "unit_cost must be greater than zero"
            )
        return value
