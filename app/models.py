from decimal import Decimal
from datetime import datetime

from app import db


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
    plate = db.Column(db.String(10), nullable=False, unique=True)
    vehicle_type = db.Column(db.String(50), nullable=False)
    brand = db.Column(db.String(80), nullable=True)
    model = db.Column(db.String(80), nullable=True)
    manufacture_year = db.Column(db.Integer, nullable=True)
    capacity_kg = db.Column(db.Numeric(10, 2), nullable=True)
    current_mileage = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default="AVAILABLE")
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    drivers = db.relationship("Driver", backref="vehicle", lazy=True)
    maintenances = db.relationship("FleetMaintenance", backref="vehicle", lazy=True)
    routes = db.relationship("Route", backref="vehicle", lazy=True)

    def __repr__(self):
        return f"<FleetVehicle {self.plate}>"


class FleetMaintenance(db.Model):
    __tablename__ = "fleet_maintenances"

    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(
        db.Integer,
        db.ForeignKey("fleet_vehicles.id"),
        nullable=False,
    )
    maintenance_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    workshop = db.Column(db.String(120), nullable=True)
    opened_at = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    scheduled_at = db.Column(db.Date, nullable=True)
    completed_at = db.Column(db.Date, nullable=True)
    mileage = db.Column(db.Integer, nullable=True)
    cost = db.Column(db.Numeric(10, 2), nullable=True)
    status = db.Column(db.String(30), nullable=False, default="OPEN")
    next_maintenance_at = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def __repr__(self):
        return f"<FleetMaintenance {self.id}>"


class Driver(db.Model):
    __tablename__ = "drivers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    cpf = db.Column(db.String(14), nullable=False, unique=True)
    phone = db.Column(db.String(30), nullable=True)
    license_number = db.Column(db.String(30), nullable=False, unique=True)
    license_category = db.Column(db.String(5), nullable=False)
    license_expiry = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="ACTIVE")
    vehicle_id = db.Column(
        db.Integer,
        db.ForeignKey("fleet_vehicles.id"),
        nullable=True,
    )
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    routes = db.relationship("Route", backref="driver", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "cpf": self.cpf,
            "phone": self.phone,
            "license_number": self.license_number,
            "license_category": self.license_category,
            "license_expiry": (
                self.license_expiry.isoformat()
                if self.license_expiry
                else None
            ),
            "status": self.status,
            "vehicle_id": self.vehicle_id,
            "vehicle_plate": (
                self.vehicle.plate
                if self.vehicle
                else None
            ),
            "notes": self.notes,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),
            "updated_at": (
                self.updated_at.isoformat()
                if self.updated_at
                else None
            ),
        }

    def __repr__(self):
        return f"<Driver {self.name}>"


class Route(db.Model):
    __tablename__ = "routes"

    id = db.Column(db.Integer, primary_key=True)
    route_name = db.Column(db.String(120), nullable=False)
    vehicle_id = db.Column(
        db.Integer,
        db.ForeignKey("fleet_vehicles.id"),
        nullable=True,
    )
    driver_id = db.Column(
        db.Integer,
        db.ForeignKey("drivers.id"),
        nullable=True,
    )
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="PENDING")
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "route_name": self.route_name,
            "vehicle_id": self.vehicle_id,
            "vehicle_plate": self.vehicle.plate if self.vehicle else None,
            "driver_id": self.driver_id,
            "driver_name": self.driver.name if self.driver else None,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "status": self.status,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Route {self.route_name}>"