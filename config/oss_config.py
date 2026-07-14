import os

OSS_CONFIG = {
    "access_key_id": os.getenv("OSS_ACCESS_KEY_ID"),
    "access_key_secret": os.getenv("OSS_ACCESS_KEY_SECRET"),
    "bucket_name": "lvmr-xlt",
    "endpoint": "https://oss-cn-beijing.aliyuncs.com",          # 公网Endpoint
    "internal_endpoint": "https://oss-cn-beijing-internal.aliyuncs.com",  # 内网Endpoint（同地域ECS可用）
    "region": "cn-beijing",
    "is_secure": True,           # 强制HTTPS
    "connect_timeout": 10,       # 连接超时(秒)
    "read_timeout": 30           # 读取超时(秒)
}

DOC_CONTENT_TYPES = {
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}