from decimal import Decimal, InvalidOperation
from flask import jsonify, Request


def get_json_dict(request: Request) -> tuple[dict | None, tuple | None]:
    """
    Extrai e valida que o corpo da requisição é estritamente um objeto JSON (dict).
    Evita falhas de Type Confusion (AttributeError quando o cliente envia lista ou primitivo).
    """
    data = request.get_json(silent=True)
    if data is None:
        # Se silent=True retornou None mas request.data continha algo que não era JSON
        if request.data and request.data.strip():
            return None, (jsonify({"error": "Invalid JSON payload"}), 400)
        return {}, None

    if not isinstance(data, dict):
        return None, (jsonify({"error": "Payload must be a JSON object"}), 400)

    return data, None


def validate_string_field(value, field_name: str, max_len: int = 100, min_len: int = 1) -> tuple[bool, str | None]:
    """
    Valida limites de tamanho de campos de texto para evitar Buffer/Memory Exhaustion.
    """
    if value is None:
        return True, None

    if not isinstance(value, str):
        return False, f"{field_name} must be a string"

    val_stripped = value.strip()
    if len(val_stripped) < min_len:
        return False, f"{field_name} cannot be empty"

    if len(val_stripped) > max_len:
        return False, f"{field_name} exceeds maximum length of {max_len} characters"

    return True, None


def validate_price_bounds(price_val, max_price: Decimal = Decimal("999999999.99")) -> tuple[bool, str | None]:
    """
    Valida sanidade numérica do preço para evitar overflow em cálculos e relatórios.
    """
    try:
        price = Decimal(str(price_val))
    except (InvalidOperation, ValueError, TypeError):
        return False, "price must be a valid number"

    if price < 0:
        return False, "price cannot be negative"

    if price > max_price:
        return False, f"price cannot exceed {max_price}"

    return True, None
