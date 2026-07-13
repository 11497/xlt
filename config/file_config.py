# 支持的文件类型
ALLOWED_FILE_TYPES = {
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

# 最大上传文件大小（10MB）
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# 上传文件过期时间（5分钟）
EXPIRES = 300  # 5分钟