from typing import List, Tuple
from openai import OpenAI
from config.ai_config import BASE_URL, RERANK_MODEL
import os


class RerankService:
    """重排序服务封装"""

    def __init__(
            self,
            model: str = RERANK_MODEL,
            base_url: str = BASE_URL
    ):
        """
        :param model: 重排序模型名称
        :param base_url: API基础地址
        """
        self.client = OpenAI(
            base_url=base_url,
            api_key=os.getenv("OPENAI_API_KEY")
        )
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

        response = self.client.rerank.create(
            model=self.model,
            query=query,
            documents=documents,
            top_n=top_n
        )

        # 返回排序后的文档和得分
        return [
            (documents[result.index], result.relevance_score)
            for result in response.results
        ]