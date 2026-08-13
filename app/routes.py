from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request

from app import db
from app.customer_models import Customer
from app.models import Product
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
from app.purchase_models import Purchase
from app.purchase_service import PurchaseError, receive_purchase
from app.purchase_models import Purchase, PurchaseItem
from app.purchase_service import PurchaseError, receive_purchase
from app.supplier_models import Supplier
from app.purchase_service import (
    PurchaseError,
    cancel_purchase,
    receive_purchase,
)


main = Blueprint("main", __name__)


def product_to_dict(product):
    return {
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "description": product.description,
        "price": str(product.price),
        "stock_quantity": product.stock_quantity,
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


def sale_to_dict(sale):
    return {
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


@main.get("/")
def index():
    return {
        "application": "AtlasERP",
        "status": "online",
        "message": "AtlasERP iniciado com sucesso",
    }


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

    product = Product(
        sku=data["sku"],
        name=data["name"],
        description=data.get("description"),
        price=price,
        stock_quantity=data.get("stock_quantity", 0),
        is_active=data.get("is_active", True),
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

    if "description" in data:
        product.description = data["description"]

    if "is_active" in data:
        product.is_active = bool(data["is_active"])

    db.session.commit()

    return jsonify(product_to_dict(product))


@main.delete("/products/<int:product_id>")
def deactivate_product(product_id):
    product = db.get_or_404(Product, product_id)
    product.is_active = False

    db.session.commit()

    return jsonify(product_to_dict(product))


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

    if Customer.query.filter_by(document=data["document"]).first():
        return jsonify({
            "error": "document already exists"
        }), 409

    if data.get("email"):
        if Customer.query.filter_by(email=data["email"]).first():
            return jsonify({
                "error": "email already exists"
            }), 409

    customer = Customer(
        document=data["document"],
        name=data["name"],
        email=data.get("email"),
        phone=data.get("phone"),
        is_active=data.get("is_active", True),
    )

    db.session.add(customer)
    db.session.commit()

    return jsonify(customer_to_dict(customer)), 201


@main.get("/customers/<int:customer_id>")
def get_customer(customer_id):
    customer = db.get_or_404(Customer, customer_id)
    return jsonify(customer_to_dict(customer))


@main.put("/customers/<int:customer_id>")
def update_customer(customer_id):
    customer = db.get_or_404(Customer, customer_id)
    data = request.get_json(silent=True) or {}

    if "document" in data:
        if not data["document"]:
            return jsonify({
                "error": "document cannot be empty"
            }), 400

        existing = Customer.query.filter(
            Customer.document == data["document"],
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
        customer.is_active = bool(data["is_active"])

    db.session.commit()

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


def apply_sale_filters(query):
    status = request.args.get("status")
    customer_id = request.args.get("customer_id")

    if status and status not in SALE_STATUSES:
        return None, (
            jsonify({"error": "invalid sale status"}),
            400,
        )

    if status:
        query = query.filter_by(status=status)

    if customer_id:
        try:
            customer_id = int(customer_id)
        except ValueError:
            return None, (
                jsonify({
                    "error": "customer_id must be an integer"
                }),
                400,
            )

        if customer_id <= 0:
            return None, (
                jsonify({
                    "error": "customer_id must be positive"
                }),
                400,
            )

        query = query.filter_by(customer_id=customer_id)

    return query, None


def parse_pagination_params():
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
    except (TypeError, ValueError):
        return None, None, (
            jsonify({
                "error": "page and per_page must be integers"
            }),
            400,
        )

    if page <= 0:
        return None, None, (
            jsonify({"error": "page must be positive"}),
            400,
        )

    if per_page <= 0:
        return None, None, (
            jsonify({"error": "per_page must be positive"}),
            400,
        )

    if per_page > 100:
        return None, None, (
            jsonify({
                "error": "per_page cannot be greater than 100"
            }),
            400,
        )

    return page, per_page, None


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

            return jsonify({
                "error": str(exc)
            }), 400

    sale.status = CONFIRMED
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

    if Supplier.query.filter_by(document=document).first():
        return jsonify(
            {"error": "supplier document already exists"}
        ), 409

    email = data.get("email")

    if email and Supplier.query.filter_by(email=email).first():
        return jsonify(
            {"error": "supplier email already exists"}
        ), 409

    supplier = Supplier(
        document=document,
        name=name,
        email=email,
        phone=data.get("phone"),
        is_active=data.get("is_active", True),
    )

    db.session.add(supplier)
    db.session.commit()

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

    for field in ("name", "email", "phone", "is_active"):
        if field in data:
            setattr(supplier, field, data[field])

    db.session.commit()

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
    supplier_id = request.args.get("supplier_id", type=int)

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