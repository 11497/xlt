from typing import List

import numpy as np
from openai import OpenAI

from config.ai_config import BASE_URL, EMBEDDING_MODEL, EMBEDDING_DIM, EMBEDDING_BATCH_SIZE


class EmbeddingService:
    """向量化服务封装"""

    def __init__(
            self,
            model: str = EMBEDDING_MODEL,
            base_url: str = BASE_URL
    ):
        """
        :param model: Embedding模型名称
        :param base_url: API基础地址
        """
        self.client = OpenAI(base_url=base_url)
        self.model = model

    def embed_texts(self, texts: List[str],
                    batch_size: int = EMBEDDING_BATCH_SIZE) -> List[List[float]]:
        """
        批量文本向量化，自动分批避免超出API单次请求限制
        :param texts: 待向量化的文本列表
        :param batch_size: 单批次最大文本数
        :return: 与输入顺序一致的向量列表
        """
        if not texts:
            return []

        all_embeddings: List[List[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            # 过滤空文本，避免API报错
            valid_batch = [t for t in batch if t.strip()]
            if not valid_batch:
                all_embeddings.extend([[0.0] * EMBEDDING_DIM] * len(batch))
                continue

            response = self.client.embeddings.create(
                model=self.model,
                input=valid_batch
            )
            # 按索引排序确保顺序与输入一致
            sorted_data = sorted(response.data, key=lambda x: x.index)
            batch_embeddings = [item.embedding for item in sorted_data]

            # 新增：向量L2归一化
            normalized_embeddings = []
            for emb in batch_embeddings:
                norm = np.linalg.norm(emb)
                if norm > 0:
                    normalized_embeddings.append((np.array(emb) / norm).tolist())
                else:
                    normalized_embeddings.append(emb)
            batch_embeddings = normalized_embeddings

            # 补全被过滤的空文本对应的零向量
            valid_idx = 0
            final_batch_embeddings = []
            for t in batch:
                if t.strip():
                    final_batch_embeddings.append(batch_embeddings[valid_idx])
                    valid_idx += 1
                else:
                    final_batch_embeddings.append([0.0] * 1024)

            all_embeddings.extend(final_batch_embeddings)

        return all_embeddings

    def embed_query(self, query: str) -> List[float]:
        """
        单条查询向量化，用于检索时与文档向量做相似度计算
        :param query: 用户查询语句
        :return: 查询向量
        """
        result = self.embed_texts([query], batch_size=1)
        return result[0]