from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request

from app import db
from app.models import Product


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
        return jsonify({"error": "price must be a valid number"}), 400

    if price < 0:
        return jsonify({"error": "price cannot be negative"}), 400

    if Product.query.filter_by(sku=data["sku"]).first():
        return jsonify({"error": "sku already exists"}), 409

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

    if "sku" in data:
        if not data["sku"]:
            return jsonify({"error": "sku cannot be empty"}), 400

        existing = Product.query.filter(
            Product.sku == data["sku"],
            Product.id != product.id,
        ).first()

        if existing:
            return jsonify({"error": "sku already exists"}), 409

        product.sku = data["sku"]

    if "name" in data:
        if not data["name"]:
            return jsonify({"error": "name cannot be empty"}), 400

        product.name = data["name"]

    if "description" in data:
        product.description = data["description"]

    if "price" in data:
        try:
            price = Decimal(str(data["price"]))
        except (InvalidOperation, ValueError):
            return jsonify({"error": "price must be a valid number"}), 400

        if price < 0:
            return jsonify({"error": "price cannot be negative"}), 400

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
