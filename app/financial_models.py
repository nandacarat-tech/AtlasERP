from decimal import Decimal
from datetime import datetime, date

from app import db


class FinancialCategory(db.Model):
    __tablename__ = "financial_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    category_type = db.Column(
        db.String(30),
        nullable=False,
        default="FIXED_COST",  # FIXED_COST, VARIABLE_COST, PAYROLL, REVENUE
    )
    description = db.Column(db.Text, nullable=True)

    transactions = db.relationship("FinancialTransaction", backref="category", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category_type": self.category_type,
            "description": self.description,
        }

    def __repr__(self):
        return f"<FinancialCategory {self.name}>"


class FinancialTransaction(db.Model):
    __tablename__ = "financial_transactions"

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    transaction_type = db.Column(
        db.String(20),
        nullable=False,
        default="EXPENSE",  # EXPENSE, REVENUE
    )
    status = db.Column(
        db.String(20),
        nullable=False,
        default="PENDING",  # PENDING, PAID, CANCELLED
    )
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("financial_categories.id"),
        nullable=True,
    )
    due_date = db.Column(db.Date, nullable=False, default=date.today)
    payment_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "amount": str(self.amount),
            "transaction_type": self.transaction_type,
            "status": self.status,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else "Outros",
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<FinancialTransaction {self.description}>"


class PayrollExpense(db.Model):
    __tablename__ = "payroll_expenses"

    id = db.Column(db.Integer, primary_key=True)
    employee_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(80), nullable=False)
    base_salary = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    charges_amount = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("0.00"))  # FGTS, INSS
    benefits_amount = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("0.00")) # VR, VT, Pl. Saúde
    status = db.Column(db.String(20), nullable=False, default="ACTIVE") # ACTIVE, INACTIVE
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @property
    def total_cost(self):
        return (self.base_salary or Decimal("0.00")) + (self.charges_amount or Decimal("0.00")) + (self.benefits_amount or Decimal("0.00"))

    def to_dict(self):
        return {
            "id": self.id,
            "employee_name": self.employee_name,
            "role": self.role,
            "base_salary": str(self.base_salary),
            "charges_amount": str(self.charges_amount),
            "benefits_amount": str(self.benefits_amount),
            "total_cost": str(self.total_cost),
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<PayrollExpense {self.employee_name}>"


class Invoice(db.Model):
    __tablename__ = "invoices"

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=True)
    invoice_number = db.Column(db.String(50), nullable=True)
    access_key = db.Column(db.String(44), nullable=True)  # Chave de Acesso da SEFAZ (44 dígitos)
    amount = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    status = db.Column(db.String(30), nullable=False, default="PENDING_EMISSION")  # PENDING_EMISSION, ISSUED, CANCELLED, ERROR
    sefaz_status_code = db.Column(db.String(10), nullable=True)
    sefaz_message = db.Column(db.Text, nullable=True)
    issued_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    sale = db.relationship("Sale", backref="invoices", lazy=True)
    customer = db.relationship("Customer", backref="invoices", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "sale_id": self.sale_id,
            "customer_id": self.customer_id,
            "customer_name": self.customer.name if self.customer else "Cliente Consumidor",
            "customer_document": self.customer.document if self.customer else "-",
            "invoice_number": self.invoice_number or f"NF-e {self.id:06d}",
            "access_key": self.access_key or "-",
            "amount": str(self.amount),
            "status": self.status,
            "sefaz_status_code": self.sefaz_status_code or "-",
            "sefaz_message": self.sefaz_message or "-",
            "issued_at": self.issued_at.isoformat() if self.issued_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Invoice {self.invoice_number}>"

