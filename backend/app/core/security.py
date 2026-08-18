import hashlib
import hmac
import secrets
from datetime import UTC, datetime

import bcrypt


def normalize_email(email: str) -> str:
    return email.strip().lower()


def validate_password(password: str) -> None:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if len(password) > 128:
        raise ValueError("Password must be 128 characters or fewer.")
    if not any(char.isupper() for char in password):
        raise ValueError("Password must include at least one uppercase letter.")
    if not any(char.islower() for char in password):
        raise ValueError("Password must include at least one lowercase letter.")
    if not any(char.isdigit() for char in password):
        raise ValueError("Password must include at least one number.")
    if not any(not char.isalnum() for char in password):
        raise ValueError("Password must include at least one special character.")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def constant_time_equals(a: str, b: str) -> bool:
    return hmac.compare_digest(str(a), str(b))


def password_version(value: datetime | None) -> str:
    if value is None:
        value = datetime.now(UTC)
    return value.astimezone(UTC).strftime("%Y%m%d%H%M%S%fZ")
