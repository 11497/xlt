import re

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


def clean_text_escapes(text: str) -> str:
    """
    清洗文本中的转义符与冗余空白，统一换行格式
    :param text: 原始文本
    :return: 清洗后的干净文本
    """
    if not text:
        return ""

    # 统一换行符：\r\n → \n，\r → \n
    cleaned = text.replace('\r\n', '\n').replace('\r', '\n')
    # 合并行内连续空白（空格、制表符）为单个空格
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    # 3个及以上连续换行合并为双换行（保留段落分隔）
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

    return cleaned.strip()


def chunk_text_by_sentence(
        text: str,
        max_chunk_size: int = MAX_CHUNK_SIZE,
        overlap: int = OVERLAP
) -> list[str]:
    """
    基于语句边界的文本切片函数
    :param text: 待切片的原始文本（会自动清洗转义符）
    :param max_chunk_size: 单个切片最大字符数
    :param overlap: 切片之间的重叠字符数
    :return: 切片后的文本列表
    """
    if not text:
        return []

    # 先清洗文本，再执行切片
    cleaned_text = clean_text_escapes(text)
    if not cleaned_text:
        return []

    # 按句子边界拆分（支持中英文标点及换行符）
    sentences = re.split(r'(?<=[。！？.!?\n])\s*', cleaned_text)
    sentences = [s.strip() for s in sentences if s.strip()]

    chunks = []
    current_chunk = ""

    for sentence in sentences:
        # 单句超长时强制截断（兜底）
        if len(sentence) > max_chunk_size:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            for i in range(0, len(sentence), max_chunk_size - overlap):
                chunks.append(sentence[i:i + max_chunk_size].strip())
            continue

        # 正常拼接：未超限则追加，超限则保存当前块并开启新块
        if len(current_chunk) + len(sentence) <= max_chunk_size:
            current_chunk += sentence
        else:
            chunks.append(current_chunk.strip())
            if 0 < overlap < len(current_chunk):
                current_chunk = current_chunk[-overlap:] + sentence
            else:
                current_chunk = sentence

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks