import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"
DATABASE_PATH = INSTANCE_DIR / "atlaserp_dev.db"


class Config:
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "dev-only-change-me",
    )

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{DATABASE_PATH.as_posix()}",
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Credenciais do ERP e Proteção do Módulo Financeiro
    ERP_ADMIN_USERNAME = os.getenv("ERP_ADMIN_USERNAME", "admin")
    ERP_ADMIN_PASSWORD = os.getenv("ERP_ADMIN_PASSWORD", "admin123")
    FINANCIAL_ACCESS_PASSWORD = os.getenv("FINANCIAL_ACCESS_PASSWORD", "financeiro123")


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    ERP_ADMIN_USERNAME = "admin"
    ERP_ADMIN_PASSWORD = "admin123"
    FINANCIAL_ACCESS_PASSWORD = "financeiro123"