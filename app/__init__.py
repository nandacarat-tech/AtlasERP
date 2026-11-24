# app/__init__.py

from flask import Flask, jsonify, request
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from app.config import Config


db = SQLAlchemy()
migrate = Migrate()


def create_app(config_object=None):
    app = Flask(__name__, static_folder='../static') # Mantendo a correção do static_folder

    if config_object:
        app.config.from_object(config_object)
    else:
        app.config.from_object(Config)

    @app.template_filter('currency_brl')
    def currency_brl_filter(val):
        if val is None:
            val = 0.0
        try:
            val = float(val)
        except (ValueError, TypeError):
            val = 0.0
        return "{:,.2f}".format(val).replace(',', 'X').replace('.', ',').replace('X', '.')

    db.init_app(app)
    migrate.init_app(app, db)

    # Importar os módulos de modelos AQUI, após db.init_app(app).
    # Isso garante que o 'db' esteja pronto quando os modelos são definidos.
    # Não importamos as classes diretamente aqui, apenas os módulos.
    from app import models
    from app import customer_models
    from app import sale_models
    from app import stock_movement_models
    from app import purchase_models
    from app import supplier_models
    from app import financial_models
    from app import auth_models
    from app import audit_models

    # Agora que os modelos foram carregados e registrados, podemos importar as rotas.
    from app.routes import main

    app.register_blueprint(main, url_prefix='/')

    # Configuracao de Proxy Reverso Confiável (Google Cloud Run / Load Balancer)
    if app.config.get("USE_PROXY_FIX", False) or app.config.get("IS_PRODUCTION", False):
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    # Injeção automática de Cabeçalhos de Segurança HTTP (OWASP / Hardening)
    @app.after_request
    def apply_security_headers(response):
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "script-src 'self' 'unsafe-inline';"
        )
        return response

    def _is_json_request():
        return (
            request.path.startswith("/api/")
            or request.is_json
            or request.headers.get("Accept") == "application/json"
            or (
                any(request.path.startswith(p) for p in [
                    "/products", "/customers", "/sales", "/purchases", "/suppliers", "/fleet"
                ])
                and not request.path.startswith("/ui/")
            )
        )

    @app.errorhandler(403)
    def handle_forbidden(e):
        if _is_json_request():
            return jsonify({"error": "Acesso não autorizado.", "status": 403}), 403
        return "<h3>403 Proibido - Acesso não autorizado para este perfil.</h3>", 403

    @app.errorhandler(404)
    def handle_not_found(e):
        if _is_json_request():
            return jsonify({"error": "Recurso não encontrado.", "status": 404}), 404
        return "<h3>404 Não Encontrado - A página solicitada não existe.</h3>", 404

    @app.errorhandler(500)
    def handle_server_error(e):
        db.session.rollback()
        if _is_json_request():
            return jsonify({"error": "Ocorreu um erro interno no servidor.", "status": 500}), 500
        return "<h3>500 Erro Interno - Ocorreu um erro inesperado no servidor.</h3>", 500

    return app