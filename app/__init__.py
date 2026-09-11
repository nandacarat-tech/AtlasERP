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

    # Agora que os modelos foram carregados e registrados, podemos importar as rotas.
    from app.routes import main

    app.register_blueprint(main, url_prefix='/')

    return app