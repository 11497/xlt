from typing import List, Dict, Any

from embedding import EmbeddingService
from chroma_service import ChromaService
from es_service import ESService


class IngestionService:
    """文档入库服务：统一处理双写 Chroma + ES"""

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.chroma_service = ChromaService()
        self.es_service = ESService()

    def ingest_document(
            self,
            knowledge_base_id: int,
            document_id: int,
            chunks: List[str]
    ) -> Dict[str, Any]:
        """
        将文档切片同时写入 Chroma 和 ES

        :param knowledge_base_id: 知识库ID
        :param document_id: 文档ID
        :param chunks: 文本切片列表
        :return: 入库结果摘要
        """
        if not chunks:
            return {"status": "skipped", "reason": "empty_chunks"}

        # === Step 1: 生成统一的 chunk_id ===
        # ⚠️ 关键：这个 ID 格式必须与检索时 merge 去重的依据一致
        chunk_ids = [f"{document_id}_{i}" for i in range(len(chunks))]

        # === Step 2: 向量化 ===
        embeddings = self.embedding_service.embed_texts(chunks)

        # === Step 3: 写入 Chroma ===
        try:
            self.chroma_service.add_document_embeddings(
                knowledge_base_id=knowledge_base_id,
                document_id=document_id,
                chunks=chunks,
                embeddings=embeddings
            )
            chroma_ok = True
        except Exception as e:
            print(f"[ERROR] Chroma write failed for doc {document_id}: {e}")
            chroma_ok = False

        # === Step 4: 写入 Elasticsearch ===
        try:
            # 确保索引存在
            self.es_service.create_index(knowledge_base_id)

            es_chunks = [
                {
                    "chunk_id": chunk_ids[i],  # ⚠️ 与 Chroma ID 完全一致
                    "content": chunks[i],
                    "doc_id": str(document_id),
                    "chunk_index": i,
                    "knowledge_base_id": str(knowledge_base_id)
                }
                for i in range(len(chunks))
            ]
            self.es_service.add_documents(kb_id=knowledge_base_id, chunks=es_chunks)
            es_ok = True
        except Exception as e:
            print(f"[ERROR] ES write failed for doc {document_id}: {e}")
            es_ok = False

        # === Step 5: 结果汇总 ===
        if chroma_ok and es_ok:
            status = "success"
        elif chroma_ok or es_ok:
            status = "partial"
        else:
            status = "failed"

        result = {
            "status": status,
            "document_id": document_id,
            "chunk_count": len(chunks),
            "chroma_ok": chroma_ok,
            "es_ok": es_ok
        }
        print(f"[Ingest] doc={document_id}, chunks={len(chunks)}, status={status}")
        return result

    def delete_document(self, knowledge_base_id: int, document_id: int) -> None:
        """
        同步删除双端数据
        """
        self.chroma_service.delete_document_embeddings(knowledge_base_id, document_id)

        # ES 按 doc_id 删除
        index_name = f"kb_{knowledge_base_id}"
        if self.es_service.client.indices.exists(index=index_name):
            self.es_service.client.delete_by_query(
                index=index_name,
                body={"query": {"term": {"doc_id": str(document_id)}}}
            )
        print(f"[Delete] doc={document_id} removed from both stores")