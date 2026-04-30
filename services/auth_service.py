from __future__ import annotations

import hashlib
import hmac
import os
import re
from dataclasses import dataclass

from config.settings import ROLES
from models.user import User, UserRepository
from utils.logger import get_logger

logger = get_logger(__name__)

PBKDF2_ITERATIONS = 200_000
SALT_BYTES = 16
HASH_ALGO = "sha256"


@dataclass
class AuthResult:
    success: bool
    user: User | None = None
    message: str = ""

def hash_password(plain: str) -> str:
    salt = os.urandom(SALT_BYTES)
    derived = hashlib.pbkdf2_hmac(HASH_ALGO, plain.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_{HASH_ALGO}${PBKDF2_ITERATIONS}${salt.hex()}${derived.hex()}"


def verify_password(plain: str, stored: str) -> bool:
    try:
        algo, iter_str, salt_hex, hash_hex = stored.split("$")
        if not algo.startswith("pbkdf2_"):
            return False
        iterations = int(iter_str)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
        derived = hashlib.pbkdf2_hmac(
            algo.split("_", 1)[1], plain.encode("utf-8"), salt, iterations
        )
        return hmac.compare_digest(derived, expected)
    except Exception:  # pragma: no cover - defensive
        logger.exception("Password verification failed")
        return False


#validation
USERNAME_RE = re.compile(r"^[a-zA-Z0-9_.-]{3,30}$")


def _validate_registration(username: str, password: str, role: str, full_name: str) -> str | None:
    if not USERNAME_RE.match(username or ""):
        return "Username must be 3–30 characters: letters, numbers, _ . -"
    if not full_name or len(full_name.strip()) < 2:
        return "Please enter your full name."
    if not password or len(password) < 6:
        return "Password must be at least 6 characters."
    if role not in ROLES:
        return "Please choose a valid role."
    return None


class AuthService:
    @staticmethod
    def login(username: str, password: str) -> AuthResult:
        username = (username or "").strip()
        if not username or not password:
            return AuthResult(False, message="Please enter username and password.")

        row = UserRepository.by_username(username)
        if not row:
            return AuthResult(False, message="No account found with that username.")

        if not verify_password(password, row["password_hash"]):
            return AuthResult(False, message="Incorrect password.")

        UserRepository.update_last_login(row["id"])
        user = User.from_row(row)
        logger.info("User '%s' logged in (role=%s)", user.username, user.role)
        return AuthResult(True, user=user, message=f"Welcome, {user.full_name}.")

    @staticmethod
    def register(
        *,
        username: str,
        password: str,
        role: str,
        full_name: str,
        email: str | None = None,
    ) -> AuthResult:
        username = (username or "").strip()
        full_name = (full_name or "").strip()
        email = (email or "").strip() or None

        err = _validate_registration(username, password, role, full_name)
        if err:
            return AuthResult(False, message=err)

        if UserRepository.by_username(username):
            return AuthResult(False, message="That username is already taken.")

        UserRepository.create(
            username=username,
            password_hash=hash_password(password),
            role=role,
            full_name=full_name,
            email=email,
        )
        row = UserRepository.by_username(username)
        return AuthResult(True, user=User.from_row(row), message="Account created.")
