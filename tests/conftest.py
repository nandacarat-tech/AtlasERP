import pytest

from app import create_app, db
from app.config import TestingConfig


@pytest.fixture
def app():
    application = create_app(TestingConfig)

    with application.app_context():
        db.create_all()
        from app.seed_auth import seed_rbac
        seed_rbac()

    yield application

    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def auto_authenticate_legacy_tests(request, client, app):
    """
    Autentica automaticamente o client de teste como ADMIN para os testes
    de regras de negócio legadas, preservando o estado anônimo nos testes
    de autenticação e controle de acesso.
    """
    module_name = request.module.__name__
    if any(auth_mod in module_name for auth_mod in [
        "test_auth_and_security",
        "test_rbac_and_audit",
        "test_rbac_routes_enforcement",
        "test_rate_limiting",
        "test_csrf_protection",
    ]):
        return

    with app.app_context():
        from app.auth_models import User, Role
        admin_role = Role.query.filter_by(name="ADMIN").first()
        admin_user = User.query.filter_by(username="system_admin").first()
        if not admin_user:
            admin_user = User(
                username="system_admin",
                email="system_admin@atlaserp.com",
                full_name="Administrador do Sistema",
                role=admin_role,
                is_superuser=True,
                is_active=True,
            )
            admin_user.set_password("AdminForte1234")
            db.session.add(admin_user)
            db.session.commit()
        admin_id = admin_user.id

    with client.session_transaction() as sess:
        sess["user_authenticated"] = True
        sess["user_id"] = admin_id
        sess["username"] = "system_admin"
        sess["is_superuser"] = True
        sess["role"] = "ADMIN"
        sess["financial_unlocked"] = True


@pytest.fixture
def unauthenticated_client(app):
    return app.test_client()


@pytest.fixture
def client_factory(app):
    def _create_client_with_role(role_name, username=None):
        cl = app.test_client()
        with app.app_context():
            from app.auth_models import User, Role
            role = Role.query.filter_by(name=role_name).first()
            uname = username or f"user_{role_name.lower()}"
            user = User.query.filter_by(username=uname).first()
            if not user:
                user = User(
                    username=uname,
                    email=f"{uname}@atlaserp.com",
                    full_name=f"Usuario {role_name}",
                    role=role,
                    is_superuser=False,
                    is_active=True,
                )
                user.set_password("SenhaForte1234")
                db.session.add(user)
                db.session.commit()
            uid = user.id

        with cl.session_transaction() as sess:
            sess["user_authenticated"] = True
            sess["user_id"] = uid
            sess["username"] = uname
            sess["role"] = role_name
            sess["is_superuser"] = False
        return cl
    return _create_client_with_role
