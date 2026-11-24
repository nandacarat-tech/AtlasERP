import os
from datetime import timedelta
from pathlib import Path

from werkzeug.security import generate_password_hash


BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"
DATABASE_PATH = INSTANCE_DIR / "atlaserp_dev.db"


class Config:
    ENV = os.getenv("FLASK_ENV", "development")
    IS_PRODUCTION = ENV == "production"

    # Em producao, SECRET_KEY e OBRIGATORIA (sem fallback aleatorio que invalida sessoes entre instancias)
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        if IS_PRODUCTION:
            raise RuntimeError("CRITICO: A variavel SECRET_KEY deve ser configurada no ambiente de producao!")
        SECRET_KEY = "dev-only-local-secret-key"

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{DATABASE_PATH.as_posix()}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Opcoes de pool do SQLAlchemy aplicaveis a bancos cliente-servidor (MySQL/PostgreSQL)
    if "sqlite" not in SQLALCHEMY_DATABASE_URI:
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "2")),
            "pool_recycle": 1800,
            "pool_pre_ping": True,
        }
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {}

    # Protecao de Sessao e Cookies
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = IS_PRODUCTION
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=int(os.getenv("SESSION_LIFETIME_HOURS", "8")))

    # Modo Demonstração / Vitrine Pública (permite acesso rápido com credenciais demo)
    ERP_DEMO_MODE = os.getenv("ERP_DEMO_MODE", "true").lower() in ("true", "1", "yes")

    # Acesso Emergencial (Break-Glass Account) - Desativado por padrao!
    ERP_EMERGENCY_ADMIN_ENABLED = os.getenv("ERP_EMERGENCY_ADMIN_ENABLED", "false").lower() in ("true", "1", "yes")
    ERP_ADMIN_USERNAME = os.getenv("ERP_ADMIN_USERNAME", "admin")

    raw_admin_pass = os.getenv("ERP_ADMIN_PASSWORD")
    if ERP_EMERGENCY_ADMIN_ENABLED and IS_PRODUCTION and not raw_admin_pass and not os.getenv("ERP_ADMIN_PASSWORD_HASH"):
        raise RuntimeError("CRITICO: ERP_ADMIN_PASSWORD deve ser configurada quando acesso emergencial estiver ativo!")
    ERP_ADMIN_PASSWORD_HASH = os.getenv("ERP_ADMIN_PASSWORD_HASH") or generate_password_hash(
        raw_admin_pass or "admin123"
    )

    raw_fin_pass = os.getenv("FINANCIAL_ACCESS_PASSWORD")
    if IS_PRODUCTION and not raw_fin_pass and not os.getenv("FINANCIAL_ACCESS_PASSWORD_HASH"):
        raise RuntimeError("CRITICO: FINANCIAL_ACCESS_PASSWORD deve ser configurada no ambiente de producao!")
    FINANCIAL_ACCESS_PASSWORD_HASH = os.getenv("FINANCIAL_ACCESS_PASSWORD_HASH") or generate_password_hash(
        raw_fin_pass or "financeiro123"
    )


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")

    # Desativa explicitamente opcoes de pool incompativeis com SQLite em memoria
    if "sqlite" in SQLALCHEMY_DATABASE_URI:
        SQLALCHEMY_ENGINE_OPTIONS = {}
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_size": 5,
            "max_overflow": 2,
            "pool_recycle": 1800,
            "pool_pre_ping": True,
        }

    ERP_EMERGENCY_ADMIN_ENABLED = True
    ERP_ADMIN_USERNAME = "admin"
    ERP_ADMIN_PASSWORD_HASH = generate_password_hash("admin123")
    FINANCIAL_ACCESS_PASSWORD_HASH = generate_password_hash("financeiro123")
