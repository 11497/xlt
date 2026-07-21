from elasticsearch import Elasticsearch

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
                    "chunk_index": {"type": "integer"}
                }
            }
        }
        if not self.client.indices.exists(index=index_name):
            self.client.indices.create(index=index_name, body=body)

    def add_documents(self, kb_id: int, chunks: list[dict]):
        """批量写入文档切片"""
        actions = [
            {"_index": f"kb_{kb_id}", "_id": c["chunk_id"], "_source": c}
            for c in chunks
        ]
        from elasticsearch.helpers import bulk
        bulk(self.client, actions)

    def search_bm25(self, kb_id: int, query: str, top_k: int = 20) -> list[dict]:
        """BM25关键词检索"""
        resp = self.client.search(
            index=f"kb_{kb_id}",
            body={"query": {"match": {"content": query}}, "size": top_k},
        )
        return [{"id": h["_id"], "score": h["_score"], "content": h["_source"]["content"]}
                for h in resp["hits"]["hits"]]