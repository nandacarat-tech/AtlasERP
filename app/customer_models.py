from sqlalchemy.orm import validates
from app import db
from app.validators import validate_document, validate_phone


class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    document = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

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

    def __repr__(self):
        return f"<Customer {self.document}>"
