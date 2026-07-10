import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any


class JwtUtil:
    """
    JWT 工具类：封装 Token 的生成、解析与验证逻辑
    """

    def __init__(self, secret_key: str, algorithm: str = "HS256", access_token_expire_minutes: int = 30):
        """
        :param secret_key: 签名密钥（务必妥善保管，不要硬编码在代码中）
        :param algorithm: 签名算法，默认 HS256
        :param access_token_expire_minutes: Access Token 过期时间（分钟）
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        生成 Access Token
        :param data: 需要放入 payload 的数据（如 user_id, role 等）
        :param expires_delta: 自定义过期时间间隔，不传则使用默认值
        :return: JWT token 字符串
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=self.access_token_expire_minutes)
        )
        # 标准声明字段
        to_encode.update({
            "exp": expire,       # 过期时间
            "iat": datetime.now(timezone.utc),  # 签发时间
            "type": "access"    # 自定义类型标识，便于区分 access/refresh
        })
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, data: Dict[str, Any], expires_days: int = 7) -> str:
        """
        生成 Refresh Token（用于无感刷新）
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=expires_days)
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh"
        })
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> Dict[str, Any]:
        """
        解析并验证 Token
        :param token: JWT token 字符串
        :return: 解码后的 payload 字典
        :raises jwt.ExpiredSignatureError: Token 已过期
        :raises jwt.InvalidTokenError: Token 无效（签名错误、格式错误等）
        """
        return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

    def verify_token(self, token: str, expected_type: str = "access") -> Optional[Dict[str, Any]]:
        """
        安全验证 Token（带类型校验），适合在中间件/装饰器中调用
        :param token: JWT token 字符串
        :param expected_type: 期望的 token 类型 ("access" / "refresh")
        :return: 有效则返回 payload，无效返回 None
        """
        try:
            payload = self.decode_token(token)
            if payload.get("type") != expected_type:
                return None
            return payload
        except jwt.ExpiredSignatureError:
            print("[JWT] Token 已过期")
            return None
        except jwt.InvalidTokenError as e:
            print(f"[JWT] Token 无效: {e}")
            return None