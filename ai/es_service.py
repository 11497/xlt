from typing import List, Dict, Any
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk


class ESService:
    def __init__(self, host="localhost", port=9200):
        self.client = Elasticsearch([{"host": host, "port": port}])

    def create_index(self, kb_id: int):
        """创建支持中文BM25的索引"""
        index_name = f"kb_{kb_id}"
        body = {
            "settings": {
                "analysis": {
                    "analyzer": {
                        "ik_analyzer": {"type": "custom", "tokenizer": "ik_max_word"}
                    }
                }
            },
            "mappings": {
                "properties": {
                    "content": {"type": "text", "analyzer": "ik_analyzer"},
                    "doc_id": {"type": "keyword"},
                    "chunk_index": {"type": "integer"},
                    # 新增：冗余存储knowledge_base_id方便过滤
                    "knowledge_base_id": {"type": "keyword"} 
                }
            }
        }
        if not self.client.indices.exists(index=index_name):
            self.client.indices.create(index=index_name, body=body)

    def add_documents(self, kb_id: int, chunks: List[Dict[str, Any]]):
        """批量写入文档切片"""
        actions = [
            {"_index": f"kb_{kb_id}", "_id": c["chunk_id"], "_source": c}
            for c in chunks
        ]
        if actions:
            bulk(self.client, actions)

    def search_bm25(self, kb_id: int, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """
        BM25关键词检索，返回标准化格式以便与向量结果合并
        """
        resp = self.client.search(
            index=f"kb_{kb_id}",
            body={
                "query": {"match": {"content": query}}, 
                "size": top_k
            },
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