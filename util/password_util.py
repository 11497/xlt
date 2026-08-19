"""密码哈希与验证工具。"""

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError


class PasswordUtil:
    """统一封装 Argon2id 密码处理。"""

    _password_hasher = PasswordHasher(type=Type.ID)

    @classmethod
    def hash_password(cls, plain_password: str) -> str:
        """将明文密码转换为带随机盐的 Argon2id 哈希。"""
        return cls._password_hasher.hash(plain_password)

    @classmethod
    def verify_password(cls, plain_password: str, password_hash: str) -> bool:
        """验证明文密码是否与 Argon2id 哈希匹配。"""
        try:
            return cls._password_hasher.verify(password_hash, plain_password)
        except (VerificationError, InvalidHashError):
            return False
