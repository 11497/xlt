from typing import List, Dict, Any
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from config.ai_config import VIRTUAL_MACHINE_HOST, ES_PORT


class ESService:
    def __init__(self, host=VIRTUAL_MACHINE_HOST, port=ES_PORT):
        self.client = Elasticsearch([{"host": host, "port": port, "scheme": "http"}])

    def create_index(self, kb_id: int):
        """创建支持中文BM25的索引"""
        index_name = f"kb_{kb_id}"
        settings = {
            "analysis": {
                "analyzer": {
                    "ik_analyzer": {"type": "custom", "tokenizer": "ik_max_word"}
                }
            }
        }
        mappings = {
            "properties": {
                "content": {"type": "text", "analyzer": "ik_analyzer"},
                "doc_id": {"type": "keyword"},
                "chunk_index": {"type": "integer"},
                # 新增：冗余存储knowledge_base_id方便过滤
                "knowledge_base_id": {"type": "keyword"} 
            }
        }
        if not self.client.indices.exists(index=index_name):
            self.client.indices.create(index=index_name, settings=settings, mappings=mappings)

    def add_documents(self, kb_id: int, chunks: List[Dict[str, Any]]):
        """批量写入文档切片（幂等，_id=chunk_id 重复写入自动覆盖）"""
        actions = [
            {"_index": f"kb_{kb_id}", "_id": c["chunk_id"], "_source": c}
            for c in chunks
        ]
        if actions:
            bulk(self.client, actions)

    def delete_document(self, kb_id: int, document_id: int) -> bool:
        """
        按 doc_id 删除某文档的所有切片（幂等）
        :param kb_id: 知识库ID
        :param document_id: 文档ID
        :return: 是否执行成功
        """
        try:
            index_name = f"kb_{kb_id}"
            if not self.client.indices.exists(index=index_name):
                return True
            resp = self.client.delete_by_query(
                index=index_name,
                query={"term": {"doc_id": str(document_id)}},
                refresh=True
            )
            return True
        except Exception as e:
            print(f"[ERROR] ES delete failed for doc {document_id}: {e}")
            return False

    def delete_knowledge_base(self, kb_id: int) -> bool:
        """
        删除整个知识库索引（幂等）
        :param kb_id: 知识库ID
        :return: 是否执行成功
        """
        try:
            index_name = f"kb_{kb_id}"
            if self.client.indices.exists(index=index_name):
                self.client.indices.delete(index=index_name)
            return True
        except Exception as e:
            print(f"[ERROR] ES delete index failed for kb {kb_id}: {e}")
            return False

    def get_document_chunk_count(self, kb_id: int, document_id: int) -> int:
        """
        获取文档在 ES 中的切片数量（对账用）
        :param kb_id: 知识库ID
        :param document_id: 文档ID
        :return: 切片数量；查询失败返回 -1
        """
        try:
            index_name = f"kb_{kb_id}"
            if not self.client.indices.exists(index=index_name):
                return 0
            resp = self.client.count(
                index=index_name,
                query={"term": {"doc_id": str(document_id)}}
            )
            return int(resp["count"])
        except Exception as e:
            print(f"[ERROR] ES chunk count failed for doc {document_id}: {e}")
            return -1

    def search_bm25(self, kb_id: int, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """
        BM25关键词检索，返回标准化格式以便与向量结果合并
        """
        resp = self.client.search(
            index=f"kb_{kb_id}",
            query={"match": {"content": query}},
            size=top_k,
        )
        results = []
        for h in resp["hits"]["hits"]:
            source = h["_source"]
            results.append({
                "id": h["_id"],
                "score": h["_score"],
                "content": source.get("content", ""),
                "metadata": {
                    "document_id": source.get("doc_id"),
                    "chunk_index": source.get("chunk_index")
                }
            })
        return results
