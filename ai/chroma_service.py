from typing import List

from pathlib import Path

import chromadb
from chromadb.config import Settings
from chromadb.api.types import QueryResult

from config.ai_config import TOPK


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PERSIST_DIRECTORY = PROJECT_ROOT / "chroma_db"


class ChromaService:
    """Chroma 向量数据库服务封装"""

    def __init__(self, persist_directory: str | Path = DEFAULT_PERSIST_DIRECTORY):
        """
        :param persist_directory: Chroma 持久化目录
        """
        # 使用项目根目录下的固定路径，避免受启动命令所在目录影响。
        self.client = chromadb.PersistentClient(
            path=str(persist_directory),
            settings=Settings(
                allow_reset=True,
                anonymized_telemetry=False  # 禁用遥测
            )
        )

    def _get_collection_name(self, knowledge_base_id: int) -> str:
        """
        根据知识库ID生成集合名称
        :param knowledge_base_id: 知识库ID
        :return: 集合名称
        """
        return f"knowledge_base_{knowledge_base_id}"

    def get_or_create_collection(self, knowledge_base_id: int) -> chromadb.Collection:
        """
        获取或创建指定知识库的集合
        :param knowledge_base_id: 知识库ID
        :return: 集合对象
        """
        collection_name = self._get_collection_name(knowledge_base_id)
        return self.client.get_or_create_collection(name=collection_name)

    def add_document_embeddings(
        self,
        knowledge_base_id: int,
        document_id: int,
        chunks: List[str],
        embeddings: List[List[float]]
    ) -> None:
        """
        向指定知识库写入文档的向量（幂等 upsert，重复写入自动覆盖）
        :param knowledge_base_id: 知识库ID
        :param document_id: 文档ID
        :param chunks: 文本片段列表
        :param embeddings: 向量列表
        """
        collection = self.get_or_create_collection(knowledge_base_id)

        # 生成唯一 ID：document_id_chunk_index
        ids = [f"{document_id}_{i}" for i in range(len(chunks))]

        # 构建元数据
        metadatas = [
            {
                "document_id": document_id,
                "knowledge_base_id": knowledge_base_id,
                "chunk_index": i
            }
            for i in range(len(chunks))
        ]

        # 使用 upsert 而非 add：同一 chunk_id 重复写入自动覆盖，天然幂等，
        # 支持索引重试和对账补写。
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )

    def query_similar(
        self,
        knowledge_base_id: int,
        query_embedding: List[float],
        n_results: int = TOPK
    ) -> QueryResult:
        """
        在指定知识库中查询相似向量
        :param knowledge_base_id: 知识库ID
        :param query_embedding: 查询向量
        :param n_results: 返回数量
        :return: 查询结果
        """
        collection = self.get_or_create_collection(knowledge_base_id)

        return collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

    def delete_document_embeddings(self, knowledge_base_id: int, document_id: int) -> bool:
        """
        删除指定文档的所有向量（幂等，不存在的 ID 不报错）
        :param knowledge_base_id: 知识库ID
        :param document_id: 文档ID
        :return: 是否执行成功
        """
        try:
            collection = self.get_or_create_collection(knowledge_base_id)
            collection.delete(where={"document_id": document_id})
            return True
        except Exception as e:
            print(f"[ERROR] Chroma delete failed for doc {document_id}: {e}")
            return False

    def delete_knowledge_base(self, knowledge_base_id: int) -> bool:
        """
        删除整个知识库的所有向量（幂等）
        :param knowledge_base_id: 知识库ID
        :return: 是否执行成功
        """
        try:
            collection_name = self._get_collection_name(knowledge_base_id)
            # 先获取所有集合名称，判断目标集合是否存在
            existing_collections = [col.name for col in self.client.list_collections()]
            if collection_name in existing_collections:
                self.client.delete_collection(collection_name)
            return True
        except Exception as e:
            print(f"[ERROR] Chroma delete collection failed for kb {knowledge_base_id}: {e}")
            return False

    def get_document_chunk_count(self, knowledge_base_id: int, document_id: int) -> int:
        """
        获取文档的向量片段数量
        :param knowledge_base_id: 知识库ID
        :param document_id: 文档ID
        :return: 片段数量
        """
        try:
            collection = self.get_or_create_collection(knowledge_base_id)
            result = collection.get(where={"document_id": document_id})
            return len(result["ids"]) if result["ids"] else 0
        except Exception as e:
            print(f"[ERROR] Chroma chunk count failed for doc {document_id}: {e}")
            return -1
