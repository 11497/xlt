import os
import requests
from typing import List, Tuple

from config.ai_config import RERANK_MODEL, BASE_URL


class RerankService:
    """SiliconFlow 重排序服务封装"""

    def __init__(
            self,
            model: str = RERANK_MODEL,
            api_key: str = os.getenv("OPENAI_API_KEY"),
            base_url: str = BASE_URL + "/rerank"
    ):
        """
        :param model: 重排序模型名称
        :param api_key: SiliconFlow API Key
        :param base_url: API 地址
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    def rerank(
            self,
            query: str,
            documents: List[str],
            top_n: int = 5
    ) -> List[Tuple[str, float]]:
        """
        对文档列表根据查询进行重排序
        :param query: 用户查询语句
        :param documents: 待重排序的文档列表
        :param top_n: 返回前N个最相关的文档
        :return: 排序后的文档与相关性得分列表
        """
        if not documents:
            return []

        # 构建请求 payload[reference:2]
        payload = {
            "model": self.model,
            "query": query,
            "documents": documents,
            "top_n": top_n,
            "return_documents": False  # 不返回文档内容，节省带宽
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()

            # 解析返回结果[reference:3][reference:4]
            return [
                (documents[item["index"]], item["relevance_score"])
                for item in result.get("results", [])
            ]

        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Rerank API 调用失败: {e}")
            # 出错时返回原始文档，得分设为0（降级处理）
            return [(doc, 0.0) for doc in documents[:top_n]]