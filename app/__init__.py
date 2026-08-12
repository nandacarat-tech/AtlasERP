import os

from dotenv import load_dotenv
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


load_dotenv()

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_class=None):
    app = Flask(__name__)

    if config_class is None:
        config_class = os.getenv(
            "FLASK_CONFIG",
            "app.config.Config",
        )

    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    from app import (
        models,
        customer_models,
        sale_models,
        stock_movement_models,
    )
    from app.routes import main

    app.register_blueprint(main)

    return app