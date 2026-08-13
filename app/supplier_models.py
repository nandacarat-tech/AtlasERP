from app import db


class Supplier(db.Model):
    __tablename__ = "suppliers"

    id = db.Column(db.Integer, primary_key=True)

    document = db.Column(
        db.String(20),
        nullable=False,
        unique=True,
    )

    name = db.Column(
        db.String(120),
        nullable=False,
    )

    email = db.Column(
        db.String(120),
        nullable=True,
        unique=True,
    )

    phone = db.Column(
        db.String(30),
        nullable=True,
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
    )
