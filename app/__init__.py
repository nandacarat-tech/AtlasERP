import os

from dotenv import load_dotenv
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_object=None):
    app = Flask(__name__)

    if config_object is not None:
        app.config.from_object(config_object)
    else:
        app.config.from_object("app.config.Config")

    db.init_app(app)
    migrate.init_app(app, db)

    from app.routes import main
    app.register_blueprint(main)

    # Importar os modelos depois que db existir.
    from app import models
    from app import customer_models
    from app import sale_models
    from app import stock_movement_models
    from app import purchase_models
    from app import supplier_models

    return app