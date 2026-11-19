# app/__init__.py

from flask import Flask
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
    # Impede que clientes forjem o IP real atraves de cabecalhos X-Forwarded-For arbitrarios
    if app.config.get("USE_PROXY_FIX", False) or app.config.get("IS_PRODUCTION", False):
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    return app