from decimal import Decimal

from app import db
from datetime import datetime


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    stock_quantity = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )

    minimum_stock = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    def __repr__(self):
        return f"<Product {self.sku}>"

class FleetVehicle(db.Model):
    __tablename__ = "fleet_vehicles"

    id = db.Column(db.Integer, primary_key=True)

    plate = db.Column(
        db.String(10),
        nullable=False,
        unique=True,
    )

    vehicle_type = db.Column(
        db.String(50),
        nullable=False,
    )

    brand = db.Column(
        db.String(80),
        nullable=True,
    )

    model = db.Column(
        db.String(80),
        nullable=True,
    )

    manufacture_year = db.Column(
        db.Integer,
        nullable=True,
    )

    capacity_kg = db.Column(
        db.Numeric(10, 2),
        nullable=True,
    )

    current_mileage = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="AVAILABLE",
    )

    notes = db.Column(
        db.Text,
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

class FleetMaintenance(db.Model):
    __tablename__ = "fleet_maintenances"

    id = db.Column(db.Integer, primary_key=True)

    vehicle_id = db.Column(
        db.Integer,
        db.ForeignKey("fleet_vehicles.id"),
        nullable=False,
    )

    maintenance_type = db.Column(
        db.String(30),
        nullable=False,
    )

    description = db.Column(
        db.Text,
        nullable=False,
    )

    workshop = db.Column(
        db.String(120),
        nullable=True,
    )

    opened_at = db.Column(
        db.Date,
        nullable=False,
        default=datetime.utcnow,
    )

    scheduled_at = db.Column(
        db.Date,
        nullable=True,
    )

    completed_at = db.Column(
        db.Date,
        nullable=True,
    )

    mileage = db.Column(
        db.Integer,
        nullable=True,
    )

    cost = db.Column(
        db.Numeric(10, 2),
        nullable=True,
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="OPEN",
    )

    next_maintenance_at = db.Column(
        db.Date,
        nullable=True,
    )

    notes = db.Column(
        db.Text,
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    vehicle = db.relationship(
        "FleetVehicle",
        backref=db.backref(
            "maintenances",
            lazy=True,
        ),
    )

    def __repr__(self):
        return f"<FleetMaintenance {self.id}>"