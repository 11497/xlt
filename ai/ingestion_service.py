from typing import List, Dict, Any

from ai.embedding import EmbeddingService
from ai.chroma_service import ChromaService
from ai.es_service import ESService


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

        写入均为幂等操作（Chroma upsert / ES _id=chunk_id），
        因此本方法可安全重试：已成功的一端重复写入无副作用，
        失败的一端会在重试时补齐，最终收敛到两端一致。

        :param knowledge_base_id: 知识库ID
        :param document_id: 文档ID
        :param chunks: 文本切片列表
        :return: 入库结果摘要（status: success/partial/failed 及各端结果）
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

    def delete_document(self, knowledge_base_id: int, document_id: int) -> Dict[str, bool]:
        """
        同步删除双端数据（幂等），逐端记录结果
        :param knowledge_base_id: 知识库ID
        :param document_id: 文档ID
        :return: {"chroma": bool, "es": bool}
        """
        chroma_ok = self.chroma_service.delete_document_embeddings(knowledge_base_id, document_id)
        es_ok = self.es_service.delete_document(knowledge_base_id, document_id)
        print(f"[Delete] doc={document_id}, chroma={chroma_ok}, es={es_ok}")
        return {"chroma": chroma_ok, "es": es_ok}

    def delete_knowledge_base(self, knowledge_base_id: int) -> Dict[str, bool]:
        """
        同步删除双端（Chroma + ES）中整个知识库的数据（幂等）
        :param knowledge_base_id: 知识库ID
        :return: {"chroma": bool, "es": bool}
        """
        chroma_ok = self.chroma_service.delete_knowledge_base(knowledge_base_id)
        es_ok = self.es_service.delete_knowledge_base(knowledge_base_id)
        print(f"[Delete] kb={knowledge_base_id}, chroma={chroma_ok}, es={es_ok}")
        return {"chroma": chroma_ok, "es": es_ok}
