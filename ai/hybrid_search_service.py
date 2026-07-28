from typing import List, Dict, Any, Tuple

from ai.chroma_service import ChromaService
from config.ai_config import TOPK, TOPN
from ai.embedding import EmbeddingService
from ai.es_service import ESService
from ai.rerank_service import RerankService


def _merge_results(
        vector_results: dict,
        bm25_results: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    融合向量检索和BM25检索结果，按ID去重
    优先保留先出现的记录（也可改为保留分数更高的）
    :param vector_results: Chroma 向量检索结果
    :param bm25_results: BM25 检索结果
    :return: 融合后的结果
    """
    seen_ids = set()
    merged = []

    # 解析 Chroma 结果
    if vector_results and vector_results.get("ids"):
        ids = vector_results["ids"][0]
        documents = vector_results["documents"][0] if vector_results.get("documents") else [""] * len(ids)
        metadatas = vector_results["metadatas"][0] if vector_results.get("metadatas") else [{}] * len(ids)

        for i, doc_id in enumerate(ids):
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                merged.append({
                    "id": doc_id,
                    "content": documents[i],
                    "metadata": metadatas[i],
                    "source": "vector"
                })

    # 合并 BM25 结果
    for doc in bm25_results:
        if doc["id"] not in seen_ids:
            seen_ids.add(doc["id"])
            merged.append({
                "id": doc["id"],
                "content": doc["content"],
                "metadata": doc.get("metadata", {}),
                "source": "bm25"
            })

    return merged


class HybridSearchService:
    """混合检索服务：BM25 + Vector + Rerank"""

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.chroma_service = ChromaService()
        self.es_service = ESService()
        self.rerank_service = RerankService()

    def search(
            self,
            knowledge_base_id: int,
            query: str,
            top_k: int = TOPK,
            top_n: int = TOPN,
            recall_multiplier: float | int = 1
    ) -> List[Dict[str, Any]]:
        """
        执行混合检索
        :param knowledge_base_id: 知识库ID
        :param query: 用户查询
        :param top_k: 最终返回数量
        :param top_n: Rerank 精排数量
        :param recall_multiplier: 召回倍数，用于扩大粗排候选池
        :return: 重排后的文档列表
        """
        recall_top_k = int(top_k * recall_multiplier)

        # Step 1: 并行双路召回
        # 这里为了代码清晰使用串行

        # 1.1 向量检索
        query_embedding = self.embedding_service.embed_query(query)
        vector_results = self.chroma_service.query_similar(
            knowledge_base_id=knowledge_base_id,
            query_embedding=query_embedding,
            n_results=recall_top_k
        )
        print("vector_results:", vector_results)

        # 1.2 BM25检索
        bm25_results = self.es_service.search_bm25(
            kb_id=knowledge_base_id,
            query=query,
            top_k=recall_top_k
        )
        print("bm25_results:", bm25_results)

        # Step 2: 结果融合与去重
        merged_docs = _merge_results(vector_results, bm25_results)

        if not merged_docs:
            return []

        # Step 3: Rerank 精排
        doc_contents = [doc["content"] for doc in merged_docs]
        reranked_results: List[Tuple[str, float]] = self.rerank_service.rerank(
            query=query,
            documents=doc_contents,
            top_n=top_n
        )
        print("reranked_results:", reranked_results)

        # Step 4: 映射回原始文档信息
        # 构建 content -> doc 的映射（注意：如果有完全重复的内容可能会丢失，建议用id映射）
        content_to_doc = {doc["content"]: doc for doc in merged_docs}

        final_results = []
        for content, score in reranked_results:
            doc = content_to_doc.get(content)
            if doc:
                doc["rerank_score"] = score
                final_results.append(doc)

        vector = 0
        bm25 = 0
        for res in final_results:
            if res["source"] == "vector":
                vector += 1
            else:
                bm25 += 1
        print("=" * 50)
        print(f"vector: {vector}, bm25: {bm25}")
        print("=" * 50)

        return final_results

