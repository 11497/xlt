# 支持的文件类型
ALLOWED_FILE_TYPES = {
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

# 最大上传文件大小
MAX_FILE_SIZE = 10 * 1024 * 1024

# 上传文件过期时间
EXPIRES = 300

# 最大文本块大小
MAX_CHUNK_SIZE = 500

# 块之间的重叠字符数
OVERLAP = 150