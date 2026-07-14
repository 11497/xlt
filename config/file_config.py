# 支持的文件类型
ALLOWED_FILE_TYPES = {
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

# 最大上传文件大小（10MB）
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# 上传文件过期时间（5分钟）
EXPIRES = 300  # 5分钟

# 最大文本块大小（1000个字符）
MAX_CHUNK_SIZE = 1000

# 块之间的重叠字符数（100个字符）
OVERLAP = 100