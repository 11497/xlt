import os
from pathlib import Path


CHAT_BASE_URL = "https://api.siliconflow.cn/v1"
UTILITY_BASE_URL = "https://api.siliconflow.cn/v1"
EMBEDDING_BASE_URL = "https://api.siliconflow.cn/v1"
RERANK_BASE_URL = "https://api.siliconflow.cn/v1"

CHAT_API_KEY = os.getenv("CHAT_API_KEY")
UTILITY_API_KEY = os.getenv("UTILITY_API_KEY")
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY")
RERANK_API_KEY = os.getenv("RERANK_API_KEY")

EMBEDDING_MODEL = "Qwen/Qwen3-Embedding-8B"
EMBEDDING_DIM = 4096
EMBEDDING_BATCH_SIZE = 10

TOPK = 20
TOPN = 5

VIRTUAL_MACHINE_HOST = os.getenv("ES_HOST")
ES_PORT = int(os.getenv("ES_PORT", "9200"))

RERANK_MODEL = "Qwen/Qwen3-Reranker-8B"

CHAT_CONFIG = {
    "CHAT_MODEL": "deepseek-ai/DeepSeek-V3.2",
    "TEMPERATURE": 0.7,
    "MAX_TOKENS": 4096,
    "TOP_P": 1.0,
    "FREQUENCY_PENALTY": 0.0,
    "PRESENCE_PENALTY": 0.0
}

UTILITY_CONFIG = {
    "CHAT_MODEL": "deepseek-ai/DeepSeek-V3.2",
    "TEMPERATURE": 0.0,
    "MAX_TOKENS": 512,
    "TOP_P": 1.0,
    "FREQUENCY_PENALTY": 0.0,
    "PRESENCE_PENALTY": 0.0
}

_PROMPT_DIR = Path(__file__).parent / "prompts"


def _load_prompt(filename: str) -> str:
    return (_PROMPT_DIR / filename).read_text(encoding="utf-8").strip()


SYSTEM_MESSAGE = _load_prompt("system.md")
SUMMARY_PROMPT = _load_prompt("summary.md")
MALICIOUS_CHECK_PROMPT = _load_prompt("malicious_check.md")
REWRITE_PROMPT = _load_prompt("rewrite.md")
