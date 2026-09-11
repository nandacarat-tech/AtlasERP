from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request, render_template

from app import db
from app.customer_models import Customer
from app.models import Driver, FleetMaintenance, FleetVehicle, Product, Route, DeliveryReturn
from app.sale_models import Sale, SaleItem
from app.sale_status import (
    CANCELLED,
    CONFIRMED,
    OPEN,
    SALE_STATUSES,
)
from app.stock_movement_models import StockMovement
from app.stock_movement_service import (
    StockMovementError,
    apply_stock_out,
)
from app.supplier_models import Supplier
from app.financial_models import (
    FinancialCategory,
    FinancialTransaction,
    PayrollExpense,
    Invoice,
)
from app.purchase_models import Purchase, PurchaseItem
from app.purchase_service import (
    PurchaseError,
    cancel_purchase,
    receive_purchase,
)
from app.purchase_status import PURCHASE_STATUSES


main = Blueprint("main", __name__)


def product_to_dict(product):
    return {
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "description": product.description,
        "price": str(product.price),
        "stock_quantity": product.stock_quantity,
        "minimum_stock": product.minimum_stock,
        "is_active": product.is_active,
    }


def customer_to_dict(customer):
    return {
        "id": customer.id,
        "document": customer.document,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "is_active": customer.is_active,
    }


def sale_to_dict(sale, include_names=False):
    data = {
        "id": sale.id,
        "customer_id": sale.customer_id,
        "status": sale.status,
        "total_amount": str(sale.total_amount),
        "items": [
            {
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": str(item.unit_price),
                "subtotal": str(item.subtotal),
            }
            for item in sale.items
        ],
    }
    if include_names:
        data["customer_name"] = sale.customer.name if sale.customer else "Cliente Não Identificado"
        for i, item in enumerate(sale.items):
            data["items"][i]["product_name"] = item.product.name if item.product else "Produto"
    return data

def supplier_to_dict(supplier):
    return {
        "id": supplier.id,
        "document": supplier.document,
        "name": supplier.name,
        "email": supplier.email,
        "phone": supplier.phone,
        "is_active": supplier.is_active,
    }


def purchase_item_to_dict(item):
    return {
        "id": item.id,
        "product_id": item.product_id,
        "quantity": item.quantity,
        "unit_cost": str(item.unit_cost),
        "subtotal": str(item.subtotal),
    }


def purchase_to_dict(purchase):
    return {
        "id": purchase.id,
        "supplier_id": purchase.supplier_id,
        "status": purchase.status,
        "total_amount": str(purchase.total_amount),
        "received_at": (
            purchase.received_at.isoformat()
            if purchase.received_at
            else None
        ),
        "created_at": (
            purchase.created_at.isoformat()
            if purchase.created_at
            else None
        ),
        "items": [
            purchase_item_to_dict(item)
            for item in purchase.items
        ],
    }


def maintenance_to_dict(maintenance):
    return {
        "id": maintenance.id,
        "vehicle_id": maintenance.vehicle_id,
        "vehicle_plate": maintenance.vehicle.plate
        if maintenance.vehicle
        else None,
        "maintenance_type": maintenance.maintenance_type,
        "description": maintenance.description,
        "workshop": maintenance.workshop,
        "opened_at": maintenance.opened_at.isoformat()
        if maintenance.opened_at
        else None,
        "scheduled_at": maintenance.scheduled_at.isoformat()
        if maintenance.scheduled_at
        else None,
        "completed_at": maintenance.completed_at.isoformat()
        if maintenance.completed_at
        else None,
        "mileage": maintenance.mileage,
        "cost": str(maintenance.cost)
        if maintenance.cost is not None
        else None,
        "status": maintenance.status,
        "next_maintenance_at": maintenance.next_maintenance_at.isoformat()
        if maintenance.next_maintenance_at
        else None,
        "notes": maintenance.notes,
        "created_at": maintenance.created_at.isoformat()
        if maintenance.created_at
        else None,
        "updated_at": maintenance.updated_at.isoformat()
        if maintenance.updated_at
        else None,
    }


def parse_optional_date(value, field_name):
    if value in (None, ""):
        return None

    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(
            f"{field_name} deve estar no formato YYYY-MM-DD"
        )


def parse_optional_decimal(value, field_name):
    if value in (None, ""):
        return None

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{field_name} deve ser um número válido")


@main.get("/")
def index():
    return jsonify({
        "application": "AtlasERP"
    })


@main.get("/dashboard")
def dashboard():
    products = Product.query.order_by(Product.id).all()
    customers = Customer.query.order_by(Customer.id).all()
    suppliers = Supplier.query.order_by(Supplier.id).all()
    sales = Sale.query.order_by(Sale.id).all()
    purchases = Purchase.query.order_by(Purchase.id).all()

    out_of_stock_products = [
        product for product in products
        if product.is_active and product.stock_quantity == 0
    ]

    low_stock_products = [
        product for product in products
        if product.is_active
        and product.stock_quantity > 0
        and product.stock_quantity <= product.minimum_stock
    ]

    inactive_products = [
        product for product in products
        if not product.is_active
    ]

    open_sales = [
        sale for sale in sales
        if sale.status == OPEN
    ]

    open_purchases = [
        purchase for purchase in purchases
        if purchase.status == "OPEN"
    ]

    # Cálculos Financeiros Didáticos
    confirmed_sales = [s for s in sales if s.status == CONFIRMED]
    total_revenue = sum((s.total_amount for s in confirmed_sales), Decimal("0.00"))

    financial_transactions = FinancialTransaction.query.all()
    expense_transactions = [t for t in financial_transactions if t.transaction_type == "EXPENSE"]
    total_expenses = sum((t.amount for t in expense_transactions), Decimal("0.00"))

    net_result = total_revenue - total_expenses

    inventory_capital = sum(
        (Decimal(str(p.stock_quantity)) * p.price for p in products if p.is_active),
        Decimal("0.00")
    )

    # Itens de Atenção (Central de Ação do Empreendedor)
    pending_bills = [t for t in expense_transactions if t.status == "PENDING"]
    pending_bills_amount = sum((t.amount for t in pending_bills), Decimal("0.00"))

    revenue_transactions = [t for t in financial_transactions if t.transaction_type == "REVENUE"]
    pending_receivables = [t for t in revenue_transactions if t.status == "PENDING"]
    pending_receivables_amount = sum((t.amount for t in pending_receivables), Decimal("0.00"))

    pending_invoices_count = Invoice.query.filter_by(status="PENDING_EMISSION").count()
    pending_returns_count = DeliveryReturn.query.filter_by(status="PENDING_RETURN").count()

    payroll_list = PayrollExpense.query.all()
    pending_payroll = [p for p in payroll_list if p.status == "PENDING"]
    pending_payroll_amount = sum((p.total_cost for p in pending_payroll), Decimal("0.00"))

    active_vehicles_count = FleetVehicle.query.filter_by(status="ACTIVE").count()
    routes_in_progress_count = Route.query.filter_by(status="IN_PROGRESS").count()
    recent_sales = [sale_to_dict(s, include_names=True) for s in Sale.query.order_by(Sale.id.desc()).limit(5).all()]

    return render_template(
        "index.html",
        products=[product_to_dict(product) for product in products],
        customers=[customer_to_dict(customer) for customer in customers],
        suppliers=[supplier_to_dict(supplier) for supplier in suppliers],
        sales=[sale_to_dict(sale) for sale in sales],
        recent_sales=recent_sales,
        purchases=[purchase_to_dict(purchase) for purchase in purchases],
        out_of_stock_products=out_of_stock_products,
        low_stock_products=low_stock_products,
        inactive_products=inactive_products,
        open_sales=open_sales,
        open_purchases=open_purchases,
        total_revenue=total_revenue,
        total_expenses=total_expenses,
        net_result=net_result,
        inventory_capital=inventory_capital,
        pending_bills_count=len(pending_bills),
        pending_bills_amount=pending_bills_amount,
        pending_receivables_count=len(pending_receivables),
        pending_receivables_amount=pending_receivables_amount,
        pending_invoices_count=pending_invoices_count,
        pending_returns_count=pending_returns_count,
        pending_payroll_count=len(pending_payroll),
        pending_payroll_amount=pending_payroll_amount,
        active_vehicles_count=active_vehicles_count,
        routes_in_progress_count=routes_in_progress_count,
    )


@main.get("/ui/products")
def products_page():
    return render_template("products.html")


@main.get("/ui/fleet")
def fleet_page():
    return render_template("fleet.html")


@main.get("/ui/fleet/vehicles")
def fleet_vehicles_page():
    return render_template("fleet_vehicles.html")


@main.get("/ui/fleet/maintenances")
def fleet_maintenances_page():
    return render_template("fleet_maintenances.html")


@main.get("/ui/fleet/drivers")
def fleet_drivers_page():
    return render_template("fleet_drivers.html")


@main.get("/ui/fleet/routes")
def fleet_routes_page():
    return render_template("fleet_routes.html")


@main.get("/ui/customers")
def customers_page():
    return render_template("customers.html")


@main.get("/ui/sales")
def sales_page():
    return render_template("sales.html")


@main.get("/ui/suppliers")
def suppliers_page():
    return render_template("suppliers.html")


@main.get("/ui/purchases")
def purchases_page():
    return render_template("purchases.html")


@main.get("/ui/financial")
def financial_page():
    return render_template("financial.html")


@main.get("/ui/financial/transactions")
def financial_transactions_page():
    return render_template("financial_transactions.html")


@main.get("/ui/financial/payroll")
def financial_payroll_page():
    return render_template("financial_payroll.html")


@main.get("/ui/financial/invoices")
def financial_invoices_page():
    return render_template("financial_invoices.html")


@main.get("/products")
def list_products():
    products = Product.query.order_by(Product.id).all()
    return jsonify([product_to_dict(product) for product in products])


@main.post("/products")
def create_product():
    data = request.get_json(silent=True) or {}

    if any(not data.get(field) for field in ("sku", "name", "price")):
        return jsonify({
            "error": "sku, name and price are required"
        }), 400

    try:
        price = Decimal(str(data["price"]))
    except (InvalidOperation, ValueError):
        return jsonify({
            "error": "price must be a valid number"
        }), 400

    if price < 0:
        return jsonify({
            "error": "price cannot be negative"
        }), 400

    if Product.query.filter_by(sku=data["sku"]).first():
        return jsonify({
            "error": "sku already exists"
        }), 409

    stock_quantity = data.get("stock_quantity", 0)
    minimum_stock = data.get("minimum_stock", 0)

    if not isinstance(minimum_stock, int):
        return jsonify({
            "error": "minimum_stock must be an integer"
        }), 400

    if minimum_stock < 0:
        return jsonify({
            "error": "minimum_stock cannot be negative"
        }), 400

    if not isinstance(stock_quantity, int):
        return jsonify({
            "error": "stock_quantity must be an integer"
        }), 400

    if stock_quantity < 0:
        return jsonify({
            "error": "stock_quantity cannot be negative"
        }), 400

    is_active = data.get("is_active", True)

    if not isinstance(is_active, bool):
        return jsonify({
            "error": "is_active must be a boolean"
        }), 400

    product = Product(
        sku=data["sku"],
        name=data["name"],
        description=data.get("description"),
        price=price,
        stock_quantity=stock_quantity,
        minimum_stock=minimum_stock,
        is_active=is_active,
    )

    db.session.add(product)
    db.session.commit()

    return jsonify(product_to_dict(product)), 201


@main.get("/products/<int:product_id>")
def get_product(product_id):
    product = db.get_or_404(Product, product_id)
    return jsonify(product_to_dict(product))


@main.put("/products/<int:product_id>")
def update_product(product_id):
    product = db.get_or_404(Product, product_id)
    data = request.get_json(silent=True) or {}

    if "name" in data:
        if not data["name"]:
            return jsonify({
                "error": "name cannot be empty"
            }), 400

        product.name = data["name"]

    if "price" in data:
        try:
            price = Decimal(str(data["price"]))
        except (InvalidOperation, ValueError):
            return jsonify({
                "error": "price must be a valid number"
            }), 400

        if price < 0:
            return jsonify({
                "error": "price cannot be negative"
            }), 400

        product.price = price

    if "stock_quantity" in data:
        if not isinstance(data["stock_quantity"], int):
            return jsonify({
                "error": "stock_quantity must be an integer"
            }), 400

        if data["stock_quantity"] < 0:
            return jsonify({
                "error": "stock_quantity cannot be negative"
            }), 400

        product.stock_quantity = data["stock_quantity"]

    if "minimum_stock" in data:
        if not isinstance(data["minimum_stock"], int):
            return jsonify({
                "error": "minimum_stock must be an integer"
            }), 400

        if data["minimum_stock"] < 0:
            return jsonify({
                "error": "minimum_stock cannot be negative"
            }), 400

        product.minimum_stock = data["minimum_stock"]

    if "description" in data:
        product.description = data["description"]

    if "is_active" in data:
        if not isinstance(data["is_active"], bool):
            return jsonify({
                "error": "is_active must be a boolean"
            }), 400

        product.is_active = data["is_active"]

    db.session.commit()

    return jsonify(product_to_dict(product))


@main.delete("/products/<int:product_id>")
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)

    product.is_active = False
    db.session.commit()

    return jsonify({
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "price": str(product.price),
        "description": product.description,
        "stock_quantity": product.stock_quantity,
        "is_active": product.is_active,
    }), 200


@main.delete("/products/<int:product_id>/permanent")
def permanently_delete_product(product_id):
    product = Product.query.get_or_404(product_id)

    db.session.delete(product)
    db.session.commit()

    return jsonify({
        "message": "Produto excluído definitivamente."
    }), 200


@main.get("/customers")
def list_customers():
    customers = Customer.query.order_by(Customer.id).all()
    return jsonify([customer_to_dict(customer) for customer in customers])


@main.post("/customers")
def create_customer():
    data = request.get_json(silent=True) or {}

    if not data.get("document") or not data.get("name"):
        return jsonify({
            "error": "document and name are required"
        }), 400

    from app.validators import validate_document, validate_phone
    is_valid_doc, formatted_doc, doc_err = validate_document(data["document"])
    if not is_valid_doc:
        return jsonify({
            "error": doc_err
        }), 400

    if Customer.query.filter_by(document=formatted_doc).first():
        return jsonify({
            "error": "document already exists"
        }), 409

    if data.get("email"):
        if Customer.query.filter_by(email=data["email"]).first():
            return jsonify({
                "error": "email already exists"
            }), 409

    try:
        customer = Customer(
            document=data["document"],
            name=data["name"],
            email=data.get("email"),
            phone=data.get("phone"),
            is_active=data.get("is_active", True),
        )

        db.session.add(customer)
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return jsonify({
            "error": str(e)
        }), 400

    return jsonify(customer_to_dict(customer)), 201


@main.get("/customers/<int:customer_id>")
def get_customer(customer_id):
    customer = db.get_or_404(Customer, customer_id)
    return jsonify(customer_to_dict(customer))


@main.put("/customers/<int:customer_id>")
def update_customer(customer_id):
    customer = db.get_or_404(Customer, customer_id)
    data = request.get_json(silent=True) or {}

    try:
        if "document" in data:
            if not data["document"]:
                return jsonify({
                    "error": "document cannot be empty"
                }), 400

            from app.validators import validate_document
            is_valid_doc, formatted_doc, doc_err = validate_document(data["document"])
            if not is_valid_doc:
                return jsonify({
                    "error": doc_err
                }), 400

            existing = Customer.query.filter(
                Customer.document == formatted_doc,
                Customer.id != customer.id,
            ).first()

            if existing:
                return jsonify({
                    "error": "document already exists"
                }), 409

            customer.document = data["document"]

        if "name" in data:
            if not data["name"]:
                return jsonify({
                    "error": "name cannot be empty"
                }), 400

            customer.name = data["name"]

        if "email" in data:
            if data["email"]:
                existing = Customer.query.filter(
                    Customer.email == data["email"],
                    Customer.id != customer.id,
                ).first()

                if existing:
                    return jsonify({
                        "error": "email already exists"
                    }), 409

            customer.email = data["email"]

        if "phone" in data:
            customer.phone = data["phone"]

        if "is_active" in data:
            if not isinstance(data["is_active"], bool):
                return jsonify({
                    "error": "is_active must be a boolean"
                }), 400

            customer.is_active = data["is_active"]

        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return jsonify({
            "error": str(e)
        }), 400

    return jsonify(customer_to_dict(customer))


@main.delete("/customers/<int:customer_id>")
def deactivate_customer(customer_id):
    customer = db.get_or_404(Customer, customer_id)
    customer.is_active = False

    db.session.commit()

    return jsonify(customer_to_dict(customer))


@main.post("/sales")
def create_sale():
    data = request.get_json(silent=True) or {}

    customer_id = data.get("customer_id")
    items_data = data.get("items")

    if not customer_id:
        return jsonify({
            "error": "customer_id is required"
        }), 400

    if not isinstance(items_data, list) or not items_data:
        return jsonify({
            "error": "items must be a non-empty list"
        }), 400

    product_ids = [item.get("product_id") for item in items_data]

    if len(product_ids) != len(set(product_ids)):
        return jsonify({
            "error": "duplicate products are not allowed"
        }), 400

    customer = db.session.get(Customer, customer_id)

    if customer is None:
        return jsonify({
            "error": "customer not found"
        }), 404

    if not customer.is_active:
        return jsonify({
            "error": "customer is inactive"
        }), 400

    validated_items = []

    for item_data in items_data:
        product_id = item_data.get("product_id")
        quantity = item_data.get("quantity")

        if not product_id or not isinstance(quantity, int):
            return jsonify({
                "error": "product_id and integer quantity are required"
            }), 400

        if quantity <= 0:
            return jsonify({
                "error": "quantity must be greater than zero"
            }), 400

        product = db.session.get(Product, product_id)

        if product is None:
            return jsonify({
                "error": "product not found"
            }), 404

        if not product.is_active:
            return jsonify({
                "error": "product is inactive"
            }), 400

        if quantity > product.stock_quantity:
            return jsonify({
                "error": f"insufficient stock for product {product.sku}"
            }), 400

        validated_items.append((product, quantity))

    sale = Sale(
        customer=customer,
        status=OPEN,
        total_amount=Decimal("0.00"),
    )

    for product, quantity in validated_items:
        sale.items.append(SaleItem(
            product=product,
            quantity=quantity,
            unit_price=product.price,
        ))

    sale.recalculate_total()

    db.session.add(sale)
    db.session.commit()

    return jsonify(sale_to_dict(sale)), 201


@main.get("/sales")
def list_sales():
    query = Sale.query.order_by(Sale.id)

    status = request.args.get("status")
    customer_id = request.args.get("customer_id")

    if status and status not in SALE_STATUSES:
        return jsonify({"error": "invalid sale status"}), 400

    if status:
        query = query.filter_by(status=status)

    if customer_id:
        try:
            customer_id = int(customer_id)
        except ValueError:
            return jsonify({
                "error": "customer_id must be an integer"
            }), 400

        if customer_id <= 0:
            return jsonify({
                "error": "customer_id must be positive"
            }), 400

        query = query.filter_by(customer_id=customer_id)

    sales = query.all()

    return jsonify([sale_to_dict(sale) for sale in sales])


@main.get("/sales/paginated")
def list_sales_paginated():
    query = Sale.query.order_by(Sale.id)

    status = request.args.get("status")
    customer_id = request.args.get("customer_id")

    if status and status not in SALE_STATUSES:
        return jsonify({"error": "invalid sale status"}), 400

    if status:
        query = query.filter_by(status=status)

    if customer_id:
        try:
            customer_id = int(customer_id)
        except ValueError:
            return jsonify({
                "error": "customer_id must be an integer"
            }), 400

        if customer_id <= 0:
            return jsonify({
                "error": "customer_id must be positive"
            }), 400

        query = query.filter_by(customer_id=customer_id)

    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
    except ValueError:
        return jsonify({
            "error": "page and per_page must be integers"
        }), 400

    if page <= 0:
        return jsonify({
            "error": "page must be positive"
        }), 400

    if per_page <= 0:
        return jsonify({
            "error": "per_page must be positive"
        }), 400

    if per_page > 100:
        return jsonify({
            "error": "per_page cannot be greater than 100"
        }), 400

    total = query.count()
    sales = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        "items": [sale_to_dict(sale) for sale in sales],
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": (total + per_page - 1) // per_page,
    })


@main.get("/sales/<int:sale_id>")
def get_sale(sale_id):
    sale = db.get_or_404(Sale, sale_id)

    return jsonify(sale_to_dict(sale))

@main.post("/sales/<int:sale_id>/confirm")
def confirm_sale(sale_id):
    sale = db.get_or_404(Sale, sale_id)

    if sale.status != OPEN:
        return jsonify({
            "error": "only open sales can be confirmed"
        }), 400

    for item in sale.items:
        product = item.product

        try:
            apply_stock_out(
                product=product,
                quantity=item.quantity,
                sale_id=sale.id,
            )
        except StockMovementError as exc:
            db.session.rollback()
            err_text = str(exc)
            if "insufficient stock" in err_text:
                err_text = f"insufficient stock: Estoque insuficiente para o produto '{product.name}' (Disponível: {product.stock_quantity}, Solicitado: {item.quantity})."

            return jsonify({
                "error": err_text
            }), 400

    sale.status = CONFIRMED

    # Automação ERP: Envia a Venda para a fila de Notas Fiscais NFe do Financeiro
    existing_inv = Invoice.query.filter_by(sale_id=sale.id).first()
    if not existing_inv:
        invoice = Invoice(
            sale_id=sale.id,
            customer_id=sale.customer_id,
            amount=sale.total_amount,
            status="PENDING_EMISSION",
        )
        db.session.add(invoice)

    db.session.commit()

    return jsonify(sale_to_dict(sale))


@main.post("/sales/<int:sale_id>/cancel")
def cancel_sale(sale_id):
    sale = db.session.get(Sale, sale_id)

    if sale is None:
        return jsonify({"error": "sale not found"}), 404

    if sale.status != OPEN:
        return jsonify({
            "error": "only open sales can be cancelled"
        }), 400

    sale.status = CANCELLED
    db.session.commit()

    return jsonify({
        "id": sale.id,
        "status": sale.status,
        "total_amount": str(sale.total_amount),
    }), 200

@main.get("/products/<int:product_id>/stock-movements")
def list_stock_movements(product_id):
    product = db.session.get(Product, product_id)

    if product is None:
        return jsonify({"error": "product not found"}), 404

    movements = db.session.scalars(
        db.select(StockMovement)
        .where(StockMovement.product_id == product_id)
        .order_by(StockMovement.created_at, StockMovement.id)
    ).all()

    return jsonify([
        {
            "id": movement.id,
            "product_id": movement.product_id,
            "sale_id": movement.sale_id,
            "movement_type": movement.movement_type,
            "quantity": movement.quantity,
            "stock_before": movement.stock_before,
            "stock_after": movement.stock_after,
            "created_at": movement.created_at.isoformat(),
        }
        for movement in movements
    ])


@main.post("/purchases/<int:purchase_id>/receive")
def receive_purchase_route(purchase_id):
    purchase = db.session.get(Purchase, purchase_id)

    if purchase is None:
        return jsonify({"error": "purchase not found"}), 404

    try:
        receive_purchase(purchase=purchase)
        db.session.commit()
    except PurchaseError as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400
    except Exception:
        db.session.rollback()
        return jsonify({"error": "could not receive purchase"}), 500

    return jsonify(
        {
            "id": purchase.id,
            "status": purchase.status,
            "total_amount": str(purchase.total_amount),
            "received_at": purchase.received_at.isoformat(),
        }
    )

@main.post("/suppliers")
def create_supplier():
    data = request.get_json(silent=True) or {}

    document = data.get("document")
    name = data.get("name")

    if not document or not name:
        return jsonify(
            {"error": "document and name are required"}
        ), 400

    from app.validators import validate_document
    is_valid_doc, formatted_doc, doc_err = validate_document(document)
    if not is_valid_doc:
        return jsonify({"error": doc_err}), 400

    if Supplier.query.filter_by(document=formatted_doc).first():
        return jsonify(
            {"error": "supplier document already exists"}
        ), 409

    email = data.get("email")

    if email and Supplier.query.filter_by(email=email).first():
        return jsonify(
            {"error": "supplier email already exists"}
        ), 409

    try:
        supplier = Supplier(
            document=document,
            name=name,
            email=email,
            phone=data.get("phone"),
            is_active=data.get("is_active", True),
        )

        db.session.add(supplier)
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

    return jsonify(supplier_to_dict(supplier)), 201

@main.get("/suppliers")
def list_suppliers():
    suppliers = Supplier.query.order_by(Supplier.id).all()
    return jsonify(
        [supplier_to_dict(supplier) for supplier in suppliers]
    )

@main.patch("/suppliers/<int:supplier_id>")
def update_supplier(supplier_id):
    supplier = db.session.get(Supplier, supplier_id)

    if supplier is None:
        return jsonify({"error": "supplier not found"}), 404

    data = request.get_json(silent=True) or {}

    if "document" in data and data["document"]:
        from app.validators import validate_document
        is_valid_doc, formatted_doc, doc_err = validate_document(data["document"])
        if not is_valid_doc:
            return jsonify({"error": doc_err}), 400

        existing = Supplier.query.filter(
            Supplier.document == formatted_doc,
            Supplier.id != supplier.id,
        ).first()

        if existing:
            return jsonify({"error": "supplier document already exists"}), 409

    if "email" in data and data["email"]:
        existing = Supplier.query.filter(
            Supplier.email == data["email"],
            Supplier.id != supplier.id,
        ).first()

        if existing:
            return jsonify({"error": "supplier email already exists"}), 409

    if "is_active" in data:
        if not isinstance(data["is_active"], bool):
            return jsonify({
                "error": "is_active must be a boolean"
            }), 400

    try:
        allowed_fields = {"document", "name", "email", "phone"}

        for field in allowed_fields:
            if field in data:
                setattr(supplier, field, data[field])

        if "is_active" in data:
            supplier.is_active = data["is_active"]

        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

    return jsonify(supplier_to_dict(supplier))

@main.post("/purchases")
def create_purchase():
    data = request.get_json(silent=True) or {}
    supplier_id = data.get("supplier_id")

    if not supplier_id:
        return jsonify(
            {"error": "supplier_id is required"}
        ), 400

    supplier = db.session.get(Supplier, supplier_id)

    if supplier is None:
        return jsonify({"error": "supplier not found"}), 404

    if not supplier.is_active:
        return jsonify({"error": "supplier is inactive"}), 400

    purchase = Purchase(
        supplier_id=supplier.id,
        status="OPEN",
        total_amount="0.00",
    )

    db.session.add(purchase)
    db.session.commit()

    return jsonify(purchase_to_dict(purchase)), 201

@main.get("/purchases")
def list_purchases():
    query = Purchase.query

    status = request.args.get("status")
    supplier_id_arg = request.args.get("supplier_id")

    if status and status not in PURCHASE_STATUSES:
        return jsonify(
            {
                "error": "invalid purchase status",
                "allowed_statuses": sorted(PURCHASE_STATUSES),
            }
        ), 400

    if supplier_id_arg is None:
        supplier_id = None
    else:
        try:
            supplier_id = int(supplier_id_arg)
        except (TypeError, ValueError):
            return jsonify(
                {
                    "error": (
                        "supplier_id must be a positive integer"
                    )
                }
            ), 400

        if supplier_id <= 0:
            return jsonify(
                {
                    "error": (
                        "supplier_id must be a positive integer"
                    )
                }
            ), 400

    page_arg = request.args.get("page")
    per_page_arg = request.args.get("per_page")

    pagination_requested = (
        page_arg is not None or per_page_arg is not None
    )

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    if status:
        query = query.filter(Purchase.status == status)

    if supplier_id is not None:
        query = query.filter(
            Purchase.supplier_id == supplier_id
        )

    if page < 1:
        return jsonify(
            {"error": "page must be greater than zero"}
        ), 400

    if per_page < 1 or per_page > 100:
        return jsonify(
            {"error": "per_page must be between 1 and 100"}
        ), 400

    if not pagination_requested:
        purchases = query.order_by(Purchase.id).all()

        return jsonify(
            [
                purchase_to_dict(purchase)
                for purchase in purchases
            ]
        )

    total = query.count()

    purchases = (
        query
        .order_by(Purchase.id)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    pages = (total + per_page - 1) // per_page

    return jsonify(
        {
            "items": [
                purchase_to_dict(purchase)
                for purchase in purchases
            ],
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": pages,
        }
    )


@main.post("/purchases/<int:purchase_id>/items")
def add_purchase_item(purchase_id):
    purchase = db.session.get(Purchase, purchase_id)

    if purchase is None:
        return jsonify({"error": "purchase not found"}), 404

    if purchase.status != "OPEN":
        return jsonify(
            {"error": "purchase is not open"}
        ), 400

    data = request.get_json(silent=True) or {}

    product_id = data.get("product_id")
    quantity = data.get("quantity")
    unit_cost = data.get("unit_cost")

    if not product_id or not isinstance(quantity, int):
        return jsonify(
            {"error": "product_id and integer quantity are required"}
        ), 400

    if quantity <= 0:
        return jsonify(
            {"error": "quantity must be greater than zero"}
        ), 400

    if unit_cost is None:
        return jsonify(
            {"error": "unit_cost is required"}
        ), 400

    try:
        unit_cost = Decimal(str(unit_cost))
    except (InvalidOperation, TypeError, ValueError):
        return jsonify(
            {"error": "unit_cost must be a valid number"}
        ), 400

    if unit_cost <= 0:
        return jsonify(
            {"error": "unit_cost must be greater than zero"}
        ), 400

    product = db.session.get(Product, product_id)

    if product is None:
        return jsonify({"error": "product not found"}), 404

    if PurchaseItem.query.filter_by(
        purchase_id=purchase.id,
        product_id=product.id,
    ).first():
        return jsonify(
            {"error": "duplicate products are not allowed"}
        ), 409

    try:
        item = PurchaseItem(
            purchase_id=purchase.id,
            product_id=product.id,
            quantity=quantity,
            unit_cost=unit_cost,
        )

        db.session.add(item)
        db.session.flush()

        purchase.recalculate_total()
        db.session.commit()

    except (ValueError, TypeError) as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400

    return jsonify(purchase_to_dict(purchase)), 201


@main.get("/suppliers/<int:supplier_id>")
def get_supplier(supplier_id):
    supplier = db.session.get(Supplier, supplier_id)

    if supplier is None:
        return jsonify({"error": "supplier not found"}), 404

    return jsonify(supplier_to_dict(supplier))

@main.get("/purchases/<int:purchase_id>")
def get_purchase(purchase_id):
    purchase = db.session.get(Purchase, purchase_id)

    if purchase is None:
        return jsonify({"error": "purchase not found"}), 404

    return jsonify(purchase_to_dict(purchase))

@main.post("/purchases/<int:purchase_id>/cancel")
def cancel_purchase_route(purchase_id):
    purchase = db.session.get(Purchase, purchase_id)

    if purchase is None:
        return jsonify({"error": "purchase not found"}), 404

    try:
        cancel_purchase(purchase=purchase)
        db.session.commit()
    except PurchaseError as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400

    return jsonify(purchase_to_dict(purchase))

FLEET_VEHICLE_STATUSES = {
    "AVAILABLE",
    "IN_USE",
    "MAINTENANCE",
    "INACTIVE",
}


def fleet_vehicle_to_dict(vehicle):
    return {
        "id": vehicle.id,
        "plate": vehicle.plate,
        "vehicle_type": vehicle.vehicle_type,
        "brand": vehicle.brand,
        "model": vehicle.model,
        "manufacture_year": vehicle.manufacture_year,
        "capacity_kg": (
            float(vehicle.capacity_kg)
            if vehicle.capacity_kg is not None
            else None
        ),
        "current_mileage": vehicle.current_mileage,
        "status": vehicle.status,
        "notes": vehicle.notes,
        "created_at": (
            vehicle.created_at.isoformat()
            if vehicle.created_at
            else None
        ),
        "updated_at": (
            vehicle.updated_at.isoformat()
            if vehicle.updated_at
            else None
        ),
    }


@main.get("/fleet/vehicles")
def list_fleet_vehicles():
    vehicles = FleetVehicle.query.order_by(FleetVehicle.id.desc()).all()

    return jsonify([
        fleet_vehicle_to_dict(vehicle)
        for vehicle in vehicles
    ])


@main.post("/fleet/vehicles")
def create_fleet_vehicle():
    data = request.get_json(silent=True) or {}

    plate = str(data.get("plate", "")).strip().upper()
    vehicle_type = str(data.get("vehicle_type", "")).strip()
    status = str(data.get("status", "AVAILABLE")).strip().upper()

    if not plate:
        return jsonify({
            "error": "A placa é obrigatória."
        }), 400

    if not vehicle_type:
        return jsonify({
            "error": "O tipo de veículo é obrigatório."
        }), 400

    if status not in FLEET_VEHICLE_STATUSES:
        return jsonify({
            "error": "Status de veículo inválido."
        }), 400

    existing_vehicle = FleetVehicle.query.filter_by(
        plate=plate
    ).first()

    if existing_vehicle:
        return jsonify({
            "error": "Já existe um veículo com essa placa."
        }), 409

    current_mileage = data.get("current_mileage", 0)
    capacity_kg = data.get("capacity_kg")
    manufacture_year = data.get("manufacture_year")

    try:
        current_mileage = int(current_mileage)

        if current_mileage < 0:
            raise ValueError

        if capacity_kg is not None:
            capacity_kg = float(capacity_kg)

            if capacity_kg < 0:
                raise ValueError

        if manufacture_year is not None:
            manufacture_year = int(manufacture_year)

    except (TypeError, ValueError):
        return jsonify({
            "error": (
                "Quilometragem, capacidade e ano "
                "devem conter valores válidos."
            )
        }), 400

    vehicle = FleetVehicle(
        plate=plate,
        vehicle_type=vehicle_type,
        brand=str(data.get("brand", "")).strip() or None,
        model=str(data.get("model", "")).strip() or None,
        manufacture_year=manufacture_year,
        capacity_kg=capacity_kg,
        current_mileage=current_mileage,
        status=status,
        notes=str(data.get("notes", "")).strip() or None,
    )

    db.session.add(vehicle)
    db.session.commit()

    return jsonify(fleet_vehicle_to_dict(vehicle)), 201


@main.get("/fleet/maintenances")
def list_fleet_maintenances():
    vehicle_id = request.args.get("vehicle_id", type=int)
    status = request.args.get("status")

    query = FleetMaintenance.query.order_by(
        FleetMaintenance.opened_at.desc(),
        FleetMaintenance.id.desc(),
    )

    if vehicle_id is not None:
        query = query.filter_by(vehicle_id=vehicle_id)

    if status:
        query = query.filter_by(status=status.upper())

    maintenances = query.all()

    return jsonify([
        maintenance_to_dict(maintenance)
        for maintenance in maintenances
    ])


@main.post("/fleet/maintenances")
def create_fleet_maintenance():
    data = request.get_json(silent=True) or {}

    required_fields = (
        "vehicle_id",
        "maintenance_type",
        "description",
    )

    missing_fields = [
        field for field in required_fields
        if data.get(field) in (None, "")
    ]

    if missing_fields:
        return jsonify({
            "error": "Campos obrigatórios ausentes",
            "fields": missing_fields,
        }), 400

    vehicle = db.session.get(FleetVehicle, data["vehicle_id"])

    if vehicle is None:
        return jsonify({
            "error": "Veículo não encontrado",
        }), 404

    try:
        maintenance = FleetMaintenance(
            vehicle_id=vehicle.id,
            maintenance_type=str(data["maintenance_type"]).upper(),
            description=str(data["description"]).strip(),
            workshop=data.get("workshop"),
            scheduled_at=parse_optional_date(
                data.get("scheduled_at"),
                "scheduled_at",
            ),
            completed_at=parse_optional_date(
                data.get("completed_at"),
                "completed_at",
            ),
            mileage=data.get("mileage"),
            cost=parse_optional_decimal(
                data.get("cost"),
                "cost",
            ),
            status=str(data.get("status") or "OPEN").upper(),
            next_maintenance_at=parse_optional_date(
                data.get("next_maintenance_at"),
                "next_maintenance_at",
            ),
            notes=data.get("notes"),
        )
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    db.session.add(maintenance)
    db.session.commit()

    return jsonify(maintenance_to_dict(maintenance)), 201


@main.get("/fleet/maintenances/<int:maintenance_id>")
def get_fleet_maintenance(maintenance_id):
    maintenance = db.session.get(FleetMaintenance, maintenance_id)

    if maintenance is None:
        return jsonify({
            "error": "Manutenção não encontrada",
        }), 404

    return jsonify(maintenance_to_dict(maintenance))


@main.put("/fleet/maintenances/<int:maintenance_id>")
def update_fleet_maintenance(maintenance_id):
    maintenance = db.session.get(FleetMaintenance, maintenance_id)

    if maintenance is None:
        return jsonify({
            "error": "Manutenção não encontrada",
        }), 404

    data = request.get_json(silent=True) or {}

    try:
        if "vehicle_id" in data:
            vehicle = db.session.get(FleetVehicle, data["vehicle_id"])

            if vehicle is None:
                return jsonify({
                    "error": "Veículo não encontrado",
                }), 404

            maintenance.vehicle_id = vehicle.id

        if "maintenance_type" in data:
            maintenance.maintenance_type = str(
                data["maintenance_type"]
            ).upper()

        if "description" in data:
            maintenance.description = str(data["description"]).strip()

        if "workshop" in data:
            maintenance.workshop = data["workshop"]

        if "scheduled_at" in data:
            maintenance.scheduled_at = parse_optional_date(
                data["scheduled_at"],
                "scheduled_at",
            )

        if "completed_at" in data:
            maintenance.completed_at = parse_optional_date(
                data["completed_at"],
                "completed_at",
            )

        if "mileage" in data:
            maintenance.mileage = data["mileage"]

        if "cost" in data:
            maintenance.cost = parse_optional_decimal(
                data["cost"],
                "cost",
            )

        if "status" in data:
            maintenance.status = str(data["status"]).upper()

        if "next_maintenance_at" in data:
            maintenance.next_maintenance_at = parse_optional_date(
                data["next_maintenance_at"],
                "next_maintenance_at",
            )

        if "notes" in data:
            maintenance.notes = data["notes"]

    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    db.session.commit()

    return jsonify(maintenance_to_dict(maintenance))


# --- Rotas da API para Frota (Motoristas) ---

DRIVER_STATUSES = {
    "ACTIVE",
    "INACTIVE",
    "SUSPENDED",
}


def driver_to_dict(driver):
    return driver.to_dict()


def route_to_dict(route):
    return route.to_dict()


@main.get("/fleet/drivers")
def list_fleet_drivers():
    drivers = Driver.query.order_by(Driver.id.desc()).all()
    return jsonify([driver.to_dict() for driver in drivers])


@main.post("/fleet/drivers")
def create_fleet_driver():
    data = request.get_json(silent=True) or {}

    required_fields = (
        "name",
        "cpf",
        "license_number",
        "license_category",
        "license_expiry",
    )

    missing_fields = [
        field for field in required_fields
        if data.get(field) in (None, "")
    ]

    if missing_fields:
        return jsonify({
            "error": "Campos obrigatórios ausentes.",
            "fields": missing_fields,
        }), 400

    name = str(data["name"]).strip()
    cpf = str(data["cpf"]).strip()
    license_number = str(data["license_number"]).strip()
    license_category = str(data["license_category"]).strip().upper()
    status = str(data.get("status") or "ACTIVE").strip().upper()

    if not name:
        return jsonify({"error": "O nome é obrigatório."}), 400

    if status not in DRIVER_STATUSES:
        return jsonify({"error": "Status de motorista inválido."}), 400

    if Driver.query.filter_by(cpf=cpf).first():
        return jsonify({"error": "Já existe um motorista com esse CPF."}), 409

    if Driver.query.filter_by(license_number=license_number).first():
        return jsonify({"error": "Já existe um motorista com esse número de CNH."}), 409

    try:
        license_expiry = parse_optional_date(data["license_expiry"], "license_expiry")
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    vehicle_id = data.get("vehicle_id")
    if vehicle_id:
        try:
            vehicle_id = int(vehicle_id)
            vehicle = db.session.get(FleetVehicle, vehicle_id)
            if not vehicle:
                return jsonify({"error": "Veículo não encontrado."}), 404
        except ValueError:
            return jsonify({"error": "ID de veículo inválido."}), 400
    else:
        vehicle_id = None

    driver = Driver(
        name=name,
        cpf=cpf,
        phone=str(data.get("phone") or "").strip() or None,
        license_number=license_number,
        license_category=license_category,
        license_expiry=license_expiry,
        status=status,
        vehicle_id=vehicle_id,
        notes=str(data.get("notes") or "").strip() or None,
    )

    db.session.add(driver)
    db.session.commit()

    return jsonify(driver.to_dict()), 201


@main.get("/fleet/drivers/<int:driver_id>")
def get_fleet_driver(driver_id):
    driver = db.session.get(Driver, driver_id)
    if driver is None:
        return jsonify({"error": "Motorista não encontrado."}), 404

    return jsonify(driver.to_dict())


@main.put("/fleet/drivers/<int:driver_id>")
def update_fleet_driver(driver_id):
    driver = db.session.get(Driver, driver_id)
    if driver is None:
        return jsonify({"error": "Motorista não encontrado."}), 404

    data = request.get_json(silent=True) or {}

    if "name" in data:
        name = str(data["name"]).strip()
        if not name:
            return jsonify({"error": "O nome não pode ficar vazio."}), 400
        driver.name = name

    if "cpf" in data:
        cpf = str(data["cpf"]).strip()
        existing = Driver.query.filter(
            Driver.cpf == cpf,
            Driver.id != driver.id,
        ).first()
        if existing:
            return jsonify({"error": "Já existe um motorista com esse CPF."}), 409
        driver.cpf = cpf

    if "phone" in data:
        driver.phone = str(data["phone"] or "").strip() or None

    if "license_number" in data:
        license_number = str(data["license_number"]).strip()
        existing = Driver.query.filter(
            Driver.license_number == license_number,
            Driver.id != driver.id,
        ).first()
        if existing:
            return jsonify({"error": "Já existe um motorista com esse número de CNH."}), 409
        driver.license_number = license_number

    if "license_category" in data:
        driver.license_category = str(data["license_category"]).strip().upper()

    if "license_expiry" in data:
        try:
            driver.license_expiry = parse_optional_date(data["license_expiry"], "license_expiry")
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

    if "status" in data:
        status = str(data["status"]).strip().upper()
        if status not in DRIVER_STATUSES:
            return jsonify({"error": "Status de motorista inválido."}), 400
        driver.status = status

    if "vehicle_id" in data:
        vehicle_id = data["vehicle_id"]
        if vehicle_id in ("", None):
            driver.vehicle_id = None
        else:
            try:
                vehicle_id = int(vehicle_id)
                vehicle = db.session.get(FleetVehicle, vehicle_id)
                if vehicle is None:
                    return jsonify({"error": "Veículo não encontrado."}), 404
                driver.vehicle_id = vehicle.id
            except ValueError:
                return jsonify({"error": "ID de veículo inválido."}), 400

    if "notes" in data:
        driver.notes = str(data["notes"] or "").strip() or None

    db.session.commit()
    return jsonify(driver.to_dict())


@main.delete("/fleet/drivers/<int:driver_id>")
def deactivate_fleet_driver(driver_id):
    driver = db.session.get(Driver, driver_id)
    if driver is None:
        return jsonify({"error": "Motorista não encontrado."}), 404

    driver.status = "INACTIVE"
    db.session.commit()

    return jsonify(driver.to_dict())


# --- Rotas da API para Frota (Rotas) ---

ROUTE_STATUSES = {
    "PENDING",
    "IN_PROGRESS",
    "COMPLETED",
    "CANCELLED",
}


@main.get("/fleet/routes")
def list_fleet_routes():
    routes = Route.query.order_by(Route.start_date.desc(), Route.id.desc()).all()
    return jsonify([route.to_dict() for route in routes])


@main.post("/fleet/routes")
def create_fleet_route():
    data = request.get_json(silent=True) or {}

    required_fields = (
        "route_name",
        "start_date",
    )

    missing_fields = [
        field for field in required_fields
        if data.get(field) in (None, "")
    ]

    if missing_fields:
        return jsonify({
            "error": "Campos obrigatórios ausentes",
            "fields": missing_fields,
        }), 400

    route_name = str(data["route_name"]).strip()
    status = str(data.get("status") or "PENDING").strip().upper()

    if status not in ROUTE_STATUSES:
        return jsonify({"error": "Status de rota inválido."}), 400

    try:
        start_date = parse_optional_date(data["start_date"], "start_date")
        end_date = parse_optional_date(data.get("end_date"), "end_date")
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    vehicle_id = data.get("vehicle_id")
    if vehicle_id in ("", None):
        vehicle_id = None
    else:
        try:
            vehicle_id = int(vehicle_id)
            vehicle = db.session.get(FleetVehicle, vehicle_id)
            if vehicle is None:
                return jsonify({"error": "Veículo não encontrado."}), 404
        except ValueError:
            return jsonify({"error": "ID de veículo inválido."}), 400

    driver_id = data.get("driver_id")
    if driver_id in ("", None):
        driver_id = None
    else:
        try:
            driver_id = int(driver_id)
            driver = db.session.get(Driver, driver_id)
            if driver is None:
                return jsonify({"error": "Motorista não encontrado."}), 404
        except ValueError:
            return jsonify({"error": "ID de motorista inválido."}), 400

    route = Route(
        route_name=route_name,
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        start_date=start_date,
        end_date=end_date,
        status=status,
        description=str(data.get("description") or "").strip() or None,
    )

    db.session.add(route)
    db.session.commit()

    return jsonify(route.to_dict()), 201


@main.get("/fleet/routes/<int:route_id>")
def get_fleet_route(route_id):
    route = db.session.get(Route, route_id)
    if route is None:
        return jsonify({"error": "Rota não encontrada."}), 404

    return jsonify(route.to_dict())


@main.put("/fleet/routes/<int:route_id>")
def update_fleet_route(route_id):
    route = db.session.get(Route, route_id)
    if route is None:
        return jsonify({"error": "Rota não encontrada."}), 404

    data = request.get_json(silent=True) or {}

    if "route_name" in data:
        route.route_name = str(data["route_name"]).strip()

    if "start_date" in data:
        try:
            route.start_date = parse_optional_date(data["start_date"], "start_date")
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

    if "end_date" in data:
        try:
            route.end_date = parse_optional_date(data["end_date"], "end_date")
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

    if "status" in data:
        status = str(data["status"]).strip().upper()
        if status not in ROUTE_STATUSES:
            return jsonify({"error": "Status de rota inválido."}), 400
        route.status = status

    if "description" in data:
        route.description = str(data["description"] or "").strip() or None

    if "vehicle_id" in data:
        vehicle_id = data["vehicle_id"]
        if vehicle_id in ("", None):
            route.vehicle_id = None
        else:
            try:
                vehicle_id = int(vehicle_id)
                vehicle = db.session.get(FleetVehicle, vehicle_id)
                if vehicle is None:
                    return jsonify({"error": "Veículo não encontrado."}), 404
                route.vehicle_id = vehicle.id
            except ValueError:
                return jsonify({"error": "ID de veículo inválido."}), 400

    if "driver_id" in data:
        driver_id = data["driver_id"]
        if driver_id in ("", None):
            route.driver_id = None
        else:
            try:
                driver_id = int(driver_id)
                driver = db.session.get(Driver, driver_id)
                if driver is None:
                    return jsonify({"error": "Motorista não encontrado."}), 404
                route.driver_id = driver.id
            except ValueError:
                return jsonify({"error": "ID de motorista inválido."}), 400

    db.session.commit()
    return jsonify(route.to_dict())


@main.delete("/fleet/routes/<int:route_id>")
def delete_fleet_route(route_id):
    route = db.session.get(Route, route_id)
    if route is None:
        return jsonify({"error": "Rota não encontrada."}), 404

    db.session.delete(route)
    db.session.commit()

    return jsonify({"message": "Rota excluída com sucesso."}), 200


# --- Rotas da API para o Módulo Financeiro ---

@main.get("/api/financial/summary")
def get_financial_summary():
    transactions = FinancialTransaction.query.filter_by(status="PAID").all()
    pending_transactions = FinancialTransaction.query.filter_by(status="PENDING").all()
    payrolls = PayrollExpense.query.filter(PayrollExpense.status != "INACTIVE").all()

    # Integração em tempo real com o Catálogo de Produtos (Estoque)
    products = Product.query.filter_by(is_active=True).all()
    total_stock_value = sum(p.stock_quantity * p.price for p in products)

    # Integração em tempo real com o Módulo de Vendas
    sales_confirmed = Sale.query.filter_by(status=CONFIRMED).all()
    sales_open = Sale.query.filter_by(status=OPEN).all()
    confirmed_sales_total = sum(s.total_amount for s in sales_confirmed)
    open_sales_total = sum(s.total_amount for s in sales_open)

    # Integração em tempo real com o Módulo de Compras (Fornecedores)
    purchases_open = Purchase.query.filter_by(status="OPEN").all()
    open_purchases_total = sum(p.total_amount for p in purchases_open)

    # Lançamentos Manuais de Receitas e Despesas
    manual_revenue = sum(t.amount for t in transactions if t.transaction_type == "REVENUE")
    total_expenses = sum(t.amount for t in transactions if t.transaction_type == "EXPENSE")
    total_payroll = sum(p.total_cost for p in payrolls)

    # Total de Receitas (Vendas Confirmadas + Receitas Manuais)
    total_revenue = confirmed_sales_total + manual_revenue

    fixed_costs = sum(t.amount for t in transactions if t.transaction_type == "EXPENSE" and t.category and t.category.category_type == "FIXED_COST")
    variable_costs = sum(t.amount for t in transactions if t.transaction_type == "EXPENSE" and t.category and t.category.category_type == "VARIABLE_COST")

    # Contas a Pagar (Compras em aberto + Lançamentos Pendentes)
    pending_payable = sum(t.amount for t in pending_transactions if t.transaction_type == "EXPENSE") + open_purchases_total
    # Contas a Receber (Vendas em aberto + Lançamentos Pendentes)
    pending_receivable = sum(t.amount for t in pending_transactions if t.transaction_type == "REVENUE") + open_sales_total

    net_result = total_revenue - (total_expenses + total_payroll)

    return jsonify({
        "total_revenue": str(total_revenue),
        "confirmed_sales_total": str(confirmed_sales_total),
        "total_expenses": str(total_expenses),
        "total_payroll": str(total_payroll),
        "total_cost": str(total_expenses + total_payroll),
        "fixed_costs": str(fixed_costs),
        "variable_costs": str(variable_costs),
        "pending_payable": str(pending_payable),
        "pending_receivable": str(pending_receivable),
        "total_stock_value": str(total_stock_value),
        "open_purchases_total": str(open_purchases_total),
        "open_sales_total": str(open_sales_total),
        "net_result": str(net_result),
    })


@main.get("/api/financial/categories")
def list_financial_categories():
    categories = FinancialCategory.query.order_by(FinancialCategory.id).all()
    if not categories:
        default_cats = [
            FinancialCategory(name="Aluguel e Condomínio", category_type="FIXED_COST", description="Custo Fixo de Instalações"),
            FinancialCategory(name="Energia e Água", category_type="FIXED_COST", description="Utilidades básicas"),
            FinancialCategory(name="Internet e Software", category_type="FIXED_COST", description="Sistemas e Conectividade"),
            FinancialCategory(name="Insumos e Matéria Prima", category_type="VARIABLE_COST", description="Produção e Operação"),
            FinancialCategory(name="Folha de Pagamento", category_type="PAYROLL", description="Salários e Encargos"),
            FinancialCategory(name="Vendas e Serviços", category_type="REVENUE", description="Receitas operacionais"),
        ]
        db.session.add_all(default_cats)
        db.session.commit()
        categories = FinancialCategory.query.order_by(FinancialCategory.id).all()

    return jsonify([c.to_dict() for c in categories])


@main.post("/api/financial/categories")
def create_financial_category():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    category_type = str(data.get("category_type", "FIXED_COST")).strip().upper()
    if not name:
        return jsonify({"error": "O nome da categoria é obrigatório."}), 400
    if FinancialCategory.query.filter_by(name=name).first():
        return jsonify({"error": "Categoria já existente."}), 409
    category = FinancialCategory(name=name, category_type=category_type, description=data.get("description"))
    db.session.add(category)
    db.session.commit()
    return jsonify(category.to_dict()), 201


@main.get("/api/financial/transactions")
def list_financial_transactions():
    trans_type = request.args.get("type")
    status = request.args.get("status")
    query = FinancialTransaction.query.order_by(FinancialTransaction.due_date.desc(), FinancialTransaction.id.desc())
    if trans_type:
        query = query.filter_by(transaction_type=trans_type.upper())
    if status:
        query = query.filter_by(status=status.upper())
    return jsonify([t.to_dict() for t in query.all()])


@main.post("/api/financial/transactions")
def create_financial_transaction():
    data = request.get_json(silent=True) or {}
    description = str(data.get("description", "")).strip()
    amount_str = data.get("amount")
    if not description or amount_str is None:
        return jsonify({"error": "Descrição e valor são obrigatórios."}), 400
    try:
        amount = Decimal(str(amount_str))
        if amount <= 0:
            raise ValueError
    except (InvalidOperation, ValueError, TypeError):
        return jsonify({"error": "O valor deve ser um número positivo."}), 400
    due_date = parse_optional_date(data.get("due_date"), "due_date") or date.today()
    payment_date = parse_optional_date(data.get("payment_date"), "payment_date")
    is_recurring = bool(data.get("is_recurring"))
    try:
        recurring_months = int(data.get("recurring_months", 1) or 1)
    except (ValueError, TypeError):
        recurring_months = 1

    if is_recurring and recurring_months > 1:
        import calendar
        created_items = []
        base_date = due_date

        for i in range(min(recurring_months, 36)):
            target_year = base_date.year + (base_date.month + i - 1) // 12
            target_month = (base_date.month + i - 1) % 12 + 1
            max_days = calendar.monthrange(target_year, target_month)[1]
            target_day = min(base_date.day, max_days)
            item_due_date = date(target_year, target_month, target_day)

            item_desc = f"{description} ({i + 1}/{recurring_months})"
            item_status = str(data.get("status", "PENDING")).upper() if i == 0 else "PENDING"
            item_pay_date = payment_date if (i == 0 and item_status == "PAID") else None

            trans = FinancialTransaction(
                description=item_desc,
                amount=amount,
                transaction_type=str(data.get("transaction_type", "EXPENSE")).upper(),
                status=item_status,
                category_id=data.get("category_id"),
                due_date=item_due_date,
                payment_date=item_pay_date,
                notes=data.get("notes"),
            )
            db.session.add(trans)
            created_items.append(trans)

        db.session.commit()
        return jsonify([t.to_dict() for t in created_items]), 201

    transaction = FinancialTransaction(
        description=description,
        amount=amount,
        transaction_type=str(data.get("transaction_type", "EXPENSE")).upper(),
        status=str(data.get("status", "PENDING")).upper(),
        category_id=data.get("category_id"),
        due_date=due_date,
        payment_date=payment_date,
        notes=data.get("notes"),
    )
    db.session.add(transaction)
    db.session.commit()
    return jsonify(transaction.to_dict()), 201


@main.put("/api/financial/transactions/<int:trans_id>")
def update_financial_transaction(trans_id):
    transaction = db.session.get(FinancialTransaction, trans_id)
    if not transaction:
        return jsonify({"error": "Lançamento não encontrado."}), 404
    data = request.get_json(silent=True) or {}
    if "description" in data:
        transaction.description = str(data["description"]).strip()
    if "amount" in data:
        try:
            amt = Decimal(str(data["amount"]))
            if amt <= 0:
                raise ValueError
            transaction.amount = amt
        except Exception:
            return jsonify({"error": "Valor inválido."}), 400
    if "status" in data:
        transaction.status = str(data["status"]).upper()
    if "payment_date" in data:
        transaction.payment_date = parse_optional_date(data["payment_date"], "payment_date")
    if "category_id" in data:
        transaction.category_id = data["category_id"]
    if "notes" in data:
        transaction.notes = data["notes"]
    db.session.commit()
    return jsonify(transaction.to_dict())


@main.delete("/api/financial/transactions/<int:trans_id>")
def delete_financial_transaction(trans_id):
    transaction = db.session.get(FinancialTransaction, trans_id)
    if not transaction:
        return jsonify({"error": "Lançamento não encontrado."}), 404
    db.session.delete(transaction)
    db.session.commit()
    return jsonify({"message": "Lançamento excluído com sucesso."}), 200


@main.get("/api/financial/payroll")
def list_payroll_expenses():
    payrolls = PayrollExpense.query.order_by(PayrollExpense.id.desc()).all()
    return jsonify([p.to_dict() for p in payrolls])


@main.post("/api/financial/payroll")
def create_payroll_expense():
    data = request.get_json(silent=True) or {}
    employee_name = str(data.get("employee_name", "")).strip()
    role = str(data.get("role", "")).strip()
    if not employee_name or not role:
        return jsonify({"error": "Nome do colaborador e cargo são obrigatórios."}), 400
    try:
        base_salary = parse_optional_decimal(data.get("base_salary"), "base_salary") or Decimal("0.00")
        charges_amount = parse_optional_decimal(data.get("charges_amount"), "charges_amount") or Decimal("0.00")
        benefits_amount = parse_optional_decimal(data.get("benefits_amount"), "benefits_amount") or Decimal("0.00")
    except ValueError as err:
        return jsonify({"error": str(err)}), 400
    payroll = PayrollExpense(
        employee_name=employee_name,
        role=role,
        base_salary=base_salary,
        charges_amount=charges_amount,
        benefits_amount=benefits_amount,
        status=str(data.get("status", "ACTIVE")).upper(),
        notes=data.get("notes"),
    )
    db.session.add(payroll)
    db.session.commit()
    return jsonify(payroll.to_dict()), 201


@main.put("/api/financial/payroll/<int:payroll_id>")
def update_payroll_expense(payroll_id):
    payroll = db.session.get(PayrollExpense, payroll_id)
    if not payroll:
        return jsonify({"error": "Colaborador/Folha não encontrado."}), 404
    data = request.get_json(silent=True) or {}
    if "employee_name" in data:
        payroll.employee_name = str(data["employee_name"]).strip()
    if "role" in data:
        payroll.role = str(data["role"]).strip()
    if "base_salary" in data:
        payroll.base_salary = parse_optional_decimal(data["base_salary"], "base_salary") or Decimal("0.00")
    if "charges_amount" in data:
        payroll.charges_amount = parse_optional_decimal(data["charges_amount"], "charges_amount") or Decimal("0.00")
    if "benefits_amount" in data:
        payroll.benefits_amount = parse_optional_decimal(data["benefits_amount"], "benefits_amount") or Decimal("0.00")
    if "status" in data:
        payroll.status = str(data["status"]).upper()
    if "notes" in data:
        payroll.notes = data["notes"]
    db.session.commit()
    return jsonify(payroll.to_dict())


@main.delete("/api/financial/payroll/<int:payroll_id>")
def delete_payroll_expense(payroll_id):
    payroll = db.session.get(PayrollExpense, payroll_id)
    if not payroll:
        return jsonify({"error": "Colaborador/Folha não encontrado."}), 404
    db.session.delete(payroll)
    db.session.commit()
    return jsonify({"message": "Registro de folha excluído com sucesso."}), 200


# --- Rotas da API para Notas Fiscais (NF-e / SEFAZ) ---

@main.get("/api/financial/invoices")
def list_financial_invoices():
    invoices = Invoice.query.order_by(Invoice.id.desc()).all()
    return jsonify([inv.to_dict() for inv in invoices])


@main.post("/api/financial/invoices/<int:invoice_id>/emit")
def emit_financial_invoice(invoice_id):
    invoice = db.session.get(Invoice, invoice_id)
    if not invoice:
        return jsonify({"error": "Nota Fiscal não encontrada."}), 404

    if invoice.status == "ISSUED":
        return jsonify({"error": "Nota Fiscal já emitida e autorizada pela SEFAZ."}), 400

    # Simulação SEFAZ: Geração de Chave de Acesso Padrão Nacional de 44 dígitos
    uf = "35"
    yymm = datetime.utcnow().strftime("%y%m")
    cnpj = "11222333000181"
    mod = "55"
    serie = "001"
    num = f"{invoice.id:09d}"
    rnd = f"{abs(hash(invoice.id)) % 100000000:09d}"[:9]
    access_key = f"{uf}{yymm}{cnpj}{mod}{serie}{num}{rnd}"[:44]

    invoice.invoice_number = f"NF-e {invoice.id:06d}"
    invoice.access_key = access_key
    invoice.status = "ISSUED"
    invoice.sefaz_status_code = "100"
    invoice.sefaz_message = "Autorizado o uso da NF-e (Ambiente de Testes SEFAZ)"
    invoice.issued_at = datetime.utcnow()

    db.session.commit()
    return jsonify(invoice.to_dict())


# --- Rotas da UI e API para Retorno de Entregas (Módulo Frota) ---

@main.get("/ui/fleet/returns")
def ui_fleet_returns():
    return render_template("fleet_returns.html")


@main.get("/api/fleet/returns")
def list_delivery_returns():
    status_filter = request.args.get("status")
    reason_filter = request.args.get("reason")

    query = DeliveryReturn.query
    if status_filter:
        query = query.filter(DeliveryReturn.status == status_filter.upper())
    if reason_filter:
        query = query.filter(DeliveryReturn.reason == reason_filter.upper())

    returns = query.order_by(DeliveryReturn.id.desc()).all()
    return jsonify([ret.to_dict() for ret in returns])


@main.post("/api/fleet/returns")
def create_delivery_return():
    data = request.get_json(silent=True) or {}

    customer_name = str(data.get("customer_name", "")).strip()
    reason = str(data.get("reason", "")).strip().upper()

    if not customer_name:
        return jsonify({"error": "Nome do cliente é obrigatório."}), 400
    if not reason:
        return jsonify({"error": "Motivo da devolução/insucesso é obrigatório."}), 400

    sale_id = data.get("sale_id")
    route_id = data.get("route_id")
    driver_id = data.get("driver_id")
    vehicle_id = data.get("vehicle_id")

    attempt_date_val = datetime.utcnow().date()
    if data.get("attempt_date"):
        try:
            attempt_date_val = datetime.strptime(str(data["attempt_date"]), "%Y-%m-%d").date()
        except ValueError:
            pass

    delivery_return = DeliveryReturn(
        sale_id=sale_id if sale_id else None,
        route_id=route_id if route_id else None,
        driver_id=driver_id if driver_id else None,
        vehicle_id=vehicle_id if vehicle_id else None,
        customer_name=customer_name,
        attempt_date=attempt_date_val,
        reason=reason,
        status=str(data.get("status", "PENDING_RETURN")).upper(),
        action_taken=data.get("action_taken"),
        notes=data.get("notes"),
    )

    db.session.add(delivery_return)
    db.session.commit()

    return jsonify(delivery_return.to_dict()), 201


@main.post("/api/fleet/returns/<int:return_id>/resolve")
def resolve_delivery_return(return_id):
    delivery_return = db.session.get(DeliveryReturn, return_id)
    if not delivery_return:
        return jsonify({"error": "Ocorrência de entrega não encontrada."}), 404

    data = request.get_json(silent=True) or {}
    new_status = str(data.get("status", "")).strip().upper()
    action_taken = data.get("action_taken")

    if not new_status:
        return jsonify({"error": "Novo status é obrigatório."}), 400

    old_status = delivery_return.status
    delivery_return.status = new_status
    if action_taken is not None:
        delivery_return.action_taken = action_taken

    # Logística Reversa Automática: Se o status for alterado para RETURNED_TO_STOCK
    if new_status == "RETURNED_TO_STOCK" and old_status != "RETURNED_TO_STOCK" and delivery_return.sale_id:
        sale = db.session.get(Sale, delivery_return.sale_id)
        if sale:
            for item in sale.items:
                product = db.session.get(Product, item.product_id)
                if product:
                    stock_before = product.stock_quantity
                    product.stock_quantity += item.quantity
                    stock_after = product.stock_quantity
                    stock_movement = StockMovement(
                        product_id=product.id,
                        sale_id=sale.id,
                        movement_type="IN",
                        quantity=item.quantity,
                        stock_before=stock_before,
                        stock_after=stock_after,
                    )
                    db.session.add(stock_movement)

    db.session.commit()
    return jsonify(delivery_return.to_dict())


@main.get("/api/fleet/returns/summary")
def get_fleet_returns_summary():
    total = DeliveryReturn.query.count()
    pending = DeliveryReturn.query.filter_by(status="PENDING_RETURN").count()
    returned_to_stock = DeliveryReturn.query.filter_by(status="RETURNED_TO_STOCK").count()
    rescheduled = DeliveryReturn.query.filter_by(status="RESCHEDULED").count()
    cancelled = DeliveryReturn.query.filter_by(status="CANCELLED").count()

    return jsonify({
        "total": total,
        "pending": pending,
        "returned_to_stock": returned_to_stock,
        "rescheduled": rescheduled,
        "cancelled": cancelled,
    })




