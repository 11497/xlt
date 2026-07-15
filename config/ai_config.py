BASE_URL = "https://api.siliconflow.cn/v1"
EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DIM = 1024
EMBEDDING_BATCH_SIZE = 10

CHROMA_N_RESULTS = 5

CHAT_CONFIG = {
    "CHAT_MODEL": "deepseek-ai/DeepSeek-V3.2",
    "TEMPERATURE": 0.7,
    "MAX_TOKENS": 4096,
    "TOP_P": 1.0,
    "FREQUENCY_PENALTY": 0.0,
    "PRESENCE_PENALTY": 0.0
}

SYSTEM_MESSAGE = """
你是一个智能助手，需要根据提供的知识库内容来回答用户的问题。

规则：
1. 你必须严格按照知识库中的内容进行回答，不得编造信息
2. 如果在知识库中找不到与用户问题相关的内容，请直接返回：知识库中没有找到
3. 回答要简洁明了，基于知识库内容给出准确的信息
"""