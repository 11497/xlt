import os


JWT_CONFIG = {
    "secret_key": os.getenv("JWT_SECRET_KEY"),
    "algorithm": "HS256",
    "access_token_expire_minutes": 1440,
}
