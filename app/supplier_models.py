from sqlalchemy.orm import validates
from app import db
from app.validators import validate_document, validate_phone


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

    @validates("document")
    def validate_document_field(self, key, value):
        is_valid, formatted, err = validate_document(value)
        if not is_valid:
            raise ValueError(err)
        return formatted

    @validates("phone")
    def validate_phone_field(self, key, value):
        if not value:
            return None
        is_valid, formatted, err = validate_phone(value)
        if not is_valid:
            raise ValueError(err)
        return formatted
