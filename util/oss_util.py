import mimetypes
from datetime import timedelta
from typing import Optional, Union

import alibabacloud_oss_v2 as oss
import alibabacloud_oss_v2.aio as oss_aio

from config.oss_config import OSS_CONFIG


class OSSUtil:
    """阿里云OSS工具类（异步SDK V2），支持文档类文件的上传、修改与删除"""

    # 支持的文档类型及其Content-Type映射
    DOC_CONTENT_TYPES = {
        ".md": "text/markdown",
        ".txt": "text/plain",
        ".pdf": "application/pdf",
        ".doc": "application/msword",
        ".docs": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    def __init__(self):
        credentials_provider = oss.credentials.StaticCredentialsProvider(
            access_key_id=OSS_CONFIG["access_key_id"],
            access_key_secret=OSS_CONFIG["access_key_secret"],
        )

        cfg = oss.config.load_default()
        cfg.credentials_provider = credentials_provider
        cfg.region = OSS_CONFIG["region"]
        cfg.endpoint = OSS_CONFIG["endpoint"]
        cfg.connect_timeout = OSS_CONFIG["connect_timeout"]
        cfg.read_timeout = OSS_CONFIG["read_timeout"]

        self._client = oss_aio.AsyncClient(cfg)
        self._bucket = OSS_CONFIG["bucket_name"]

    async def close(self):
        """关闭客户端连接，避免资源泄漏"""
        if self._client:
            await self._client.close()

    def _get_content_type(self, object_key: str) -> str:
        """根据文件后缀获取Content-Type，优先使用自定义映射"""
        ext = "." + object_key.rsplit(".", 1)[-1].lower() if "." in object_key else ""
        if ext in self.DOC_CONTENT_TYPES:
            return self.DOC_CONTENT_TYPES[ext]
        content_type, _ = mimetypes.guess_type(object_key)
        return content_type or "application/octet-stream"

    async def upload_file(
        self,
        object_key: str,
        data: Union[bytes, str],
        content_type: Optional[str] = None,
    ) -> dict:
        """
        上传文件到OSS
        :param object_key: 对象键（如 docs/readme.md）
        :param data: 文件内容，支持bytes或str（str将自动编码为UTF-8）
        :param content_type: 自定义Content-Type，不传则自动识别
        :return: 包含status_code、request_id、etag的结果字典
        """
        if isinstance(data, str):
            data = data.encode("utf-8")

        ct = content_type or self._get_content_type(object_key)

        result = await self._client.put_object(
            oss.PutObjectRequest(
                bucket=self._bucket,
                key=object_key,
                body=data,
                content_type=ct,
            )
        )
        return {
            "status_code": result.status_code,
            "request_id": result.request_id,
            "etag": result.etag,
        }

    async def update_file(
        self,
        object_key: str,
        data: Union[bytes, str],
        content_type: Optional[str] = None,
    ) -> dict:
        """
        修改文件（覆盖更新）
        OSS中对象不可变，修改即重新上传同名对象，会自动覆盖旧版本
        :param object_key: 对象键
        :param data: 新的文件内容
        :param content_type: 自定义Content-Type，不传则自动识别
        :return: 上传结果字典
        """
        return await self.upload_file(object_key, data, content_type)

    async def delete_file(self, object_key: str) -> dict:
        """
        删除文件
        :param object_key: 对象键
        :return: 包含status_code、request_id的结果字典
        """
        result = await self._client.delete_object(
            oss.DeleteObjectRequest(
                bucket=self._bucket,
                key=object_key,
            )
        )
        return {
            "status_code": result.status_code,
            "request_id": result.request_id,
        }

    async def get_file(self, object_key: str) -> dict:
        """
        读取/下载文件内容
        :param object_key: 对象键（如 docs/readme.md）
        :return: 包含content(bytes)、content_type、etag、last_modified等信息的字典
                 文件不存在时返回 {"exists": False}
        """
        try:
            result = await self._client.get_object(
                oss.GetObjectRequest(
                    bucket=self._bucket,
                    key=object_key,
                )
            )
            body = await result.body.read()
            return {
                "exists": True,
                "content": body,
                "content_type": result.content_type,
                "etag": result.etag,
                "last_modified": result.last_modified,
                "content_length": result.content_length,
                "request_id": result.request_id,
            }
        except oss.exceptions.OperationError as e:
            # 404 表示文件不存在，不抛异常，便于业务层判断
            if hasattr(e, 'status_code') and e.status_code == 404:
                return {"exists": False}
            raise

    async def get_file_text(self, object_key: str, encoding: str = "utf-8") -> dict:
        """
        以文本形式读取文件，适用于md/txt等文本类文档的在线编辑场景
        :param object_key: 对象键
        :param encoding: 文本编码，默认UTF-8
        :return: 包含text(str)、content_type等信息的字典；文件不存在时返回 {"exists": False}
        """
        result = await self.get_file(object_key)
        if not result.get("exists"):
            return result
        try:
            result["text"] = result["content"].decode(encoding)
        except UnicodeDecodeError:
            result["text"] = None
            result["decode_error"] = f"无法以{encoding}解码，请尝试其他编码或使用get_file获取原始字节"
        return result

    async def generate_presigned_url(
            self, object_key: str, expires: int = 300
    ) -> dict:
        """
        生成预签名URL，用于在阻止公共访问的Bucket中实现临时预览/下载
        :param object_key: 对象键
        :param expires: URL有效期（秒），默认1小时
        :return: 包含url和expires的字典
        """
        # 将整数秒数转换为 timedelta 对象
        expires_delta = timedelta(seconds=expires)

        result = await self._client.presign(
            oss.GetObjectRequest(
                bucket=self._bucket,
                key=object_key,
            ),
            expires=expires_delta,  # 使用 timedelta 类型
        )
        return {
            "url": result.url,
            "expires": expires,
            "method": result.method,
        }

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()