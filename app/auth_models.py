from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

from app import db


# Tabela associativa Many-to-Many entre Perfis (Roles) e Permissoes (Permissions)
role_permissions = db.Table(
    "role_permissions",
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    db.Column("permission_id", db.Integer, db.ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class Permission(db.Model):
    __tablename__ = "permissions"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(80), unique=True, nullable=False, index=True)
    module = db.Column(db.String(40), nullable=False)
    description = db.Column(db.String(200), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "module": self.module,
            "description": self.description,
        }

    def __repr__(self):
        return f"<Permission {self.code}>"


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.String(200), nullable=True)

    users = db.relationship("User", back_populates="role", lazy="select")
    permissions = db.relationship(
        "Permission",
        secondary=role_permissions,
        backref=db.backref("roles", lazy="dynamic"),
        lazy="joined",
    )

    def has_permission(self, permission_code: str) -> bool:
        return any(perm.code == permission_code for perm in self.permissions)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "permissions": [p.code for p in self.permissions],
        }

    def __repr__(self):
        return f"<Role {self.name}>"


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(150), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_superuser = db.Column(db.Boolean, default=False, nullable=False)

    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=True)
    role = db.relationship("Role", back_populates="users", lazy="joined")

    # Protecao contra forca bruta
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime, nullable=True)

    last_login_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def set_password(self, password: str) -> None:
        if not password or len(password) < 12:
            raise ValueError("A senha deve conter no minimo 12 caracteres.")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash or not password:
            return False
        return check_password_hash(self.password_hash, password)

    def is_locked(self) -> bool:
        if self.locked_until:
            now = datetime.now(timezone.utc)
            # Normaliza fuso caso o banco retorne naive datetime
            lock_time = self.locked_until
            if lock_time.tzinfo is None:
                lock_time = lock_time.replace(tzinfo=timezone.utc)
            if lock_time > now:
                return True
        return False

    def can(self, permission_code: str) -> bool:
        if not self.is_active:
            return False
        if self.is_superuser:
            return True
        if self.role:
            return self.role.has_permission(permission_code)
        return False

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "role": self.role.name if self.role else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<User {self.username}>"


class EmergencyAdminIdentity:
    """
    Identidade estrita para o Administrador Emergencial (Break-Glass Account).
    Possui apenas permissões explícitas de recuperação de desastres (gestão de usuários e auditoria),
    NÃO permitindo contornar aprovações financeiras ou regras de negócio sem rastreio explícito.
    """
    id = None
    username = "emergency_admin"
    is_active = True
    is_superuser = False

    def __init__(self, username="emergency_admin"):
        self.username = username

    def can(self, permission_code: str) -> bool:
        allowed_recovery_permissions = {
            "users.manage",
            "users.view",
            "users.create",
            "users.edit",
            "audit.view",
        }
        return permission_code in allowed_recovery_permissions

    def is_locked(self) -> bool:
        return False

    def __repr__(self):
        return f"<EmergencyAdminIdentity {self.username}>"

