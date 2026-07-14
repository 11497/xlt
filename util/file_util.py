import subprocess

from fastapi import UploadFile
from typing import Optional
import io
import pdfplumber
from docx import Document

from config.file_config import MAX_CHUNK_SIZE, OVERLAP


async def read_file_content(file: UploadFile) -> Optional[str]:
    """
    根据文件后缀自动读取文件内容
    :param file: 需要读取的文件对象
    :return: 文件内容字符串，如果无法读取则返回 None
    """
    filename = file.filename
    if not filename:
        return None
    # 获取文件后缀
    file_ext = filename.split('.')[-1].lower()
    # 读取文件内容
    content = await file.read()

    try:
        if file_ext in ['md', 'txt']:
            # 直接读取文本文件
            return content.decode('utf-8', errors='replace')
        elif file_ext == 'pdf':
            return _read_pdf_content(content)
        elif file_ext == 'docx':
            return _read_docx_content(content)
        else:
            return None
    except Exception as e:
        print(f"读取文件失败: {e}")
        return None

def _read_pdf_content(content: bytes) -> str:
    """读取 PDF 文件内容"""
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()

def _read_docx_content(content: bytes) -> str:
    """读取 DOCX 文件内容"""
    doc = Document(io.BytesIO(content))
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text.strip()