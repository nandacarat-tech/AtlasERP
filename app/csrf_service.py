import secrets
import hmac
from urllib.parse import urlparse
from functools import wraps
from flask import session, request, abort, current_app, jsonify


def generate_csrf_token() -> str:
    """
    Gera ou recupera o token anti-CSRF criptográfico associado à sessão atual.
    """
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]


def validate_csrf_token(token: str) -> bool:
    """
    Valida um token CSRF contra o token gravado na sessão do usuário.
    Utiliza comparação de tempo constante (hmac.compare_digest) contra timing attacks.
    """
    if not token or not isinstance(token, str):
        return False
    session_token = session.get("csrf_token")
    if not session_token or not isinstance(session_token, str):
        return False
    return hmac.compare_digest(token.strip(), session_token.strip())


def csrf_protect(f):
    """
    Decorator defensivo para exigir token CSRF válido em submissões de formulários nativos.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Em modo de teste (pytest), se ENFORCE_CSRF_IN_TESTS não estiver ligado,
        # valida o token estritamente se ele for fornecido, mas não bloqueia testes legados de negócio
        is_testing = current_app.config.get("TESTING", False)
        enforce_in_test = current_app.config.get("ENFORCE_CSRF_IN_TESTS", False)

        if is_testing and not enforce_in_test:
            token = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
            if token is not None:
                if not validate_csrf_token(token):
                    return ("Acesso bloqueado: Token CSRF inválido.", 403)
            return f(*args, **kwargs)

        if request.method in ("POST", "PUT", "DELETE", "PATCH"):
            token = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
            if not validate_csrf_token(token):
                if request.is_json or request.path.startswith("/api/"):
                    return jsonify({"error": "Token CSRF inválido ou ausente."}), 403
                return ("Acesso bloqueado: Token CSRF inválido ou ausente.", 403)
        return f(*args, **kwargs)
    return decorated_function


def validate_request_origin() -> bool:
    """
    Valida os cabeçalhos W3C Sec-Fetch-Site, Origin e Referer para bloquear
    ataques de Cross-Site Request Forgery em métodos que alteram estado.
    """
    # Métodos de leitura são seguros contra CSRF por padrão
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return True

    # 1. Validação estrita via W3C Fetch Metadata (suportado por todos navegadores modernos)
    sec_fetch_site = request.headers.get("Sec-Fetch-Site")
    if sec_fetch_site:
        if sec_fetch_site.lower() == "cross-site":
            return False
        if sec_fetch_site.lower() in ("same-origin", "same-site", "none"):
            return True

    # 2. Validação de Origin (se presente)
    origin = request.headers.get("Origin")
    if origin:
        parsed_origin = urlparse(origin)
        if parsed_origin.netloc and parsed_origin.netloc.lower() != request.host.lower():
            return False

    # 3. Validação de Referer (fallback se Origin não estiver presente)
    referer = request.headers.get("Referer")
    if not origin and referer:
        parsed_referer = urlparse(referer)
        if parsed_referer.netloc and parsed_referer.netloc.lower() != request.host.lower():
            return False

    return True
