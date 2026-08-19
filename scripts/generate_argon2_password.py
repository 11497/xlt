"""将硬编码的明文密码转换为 Argon2id 哈希并打印。"""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from util.password_util import PasswordUtil  # noqa: E402


PLAINTEXT_PASSWORD = "123456"


def main() -> None:
    print(PasswordUtil.hash_password(PLAINTEXT_PASSWORD))


if __name__ == "__main__":
    main()
