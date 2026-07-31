import os

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv


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

    from app import models
    from app.routes import main

    app.register_blueprint(main)

    return app
