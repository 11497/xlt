"""将硬编码的明文密码转换为 Argon2id 哈希并打印。"""

from argon2 import PasswordHasher, Type


PLAINTEXT_PASSWORD = "123456"


def main() -> None:
    password_hasher = PasswordHasher(type=Type.ID)
    print(password_hasher.hash(PLAINTEXT_PASSWORD))


if __name__ == "__main__":
    main()
