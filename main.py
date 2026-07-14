from fastapi import FastAPI, UploadFile, File

from ai.chroma_service import ChromaService
from ai.embedding import EmbeddingService
from authentication import authentication
from model.result import Result
from router import user_router, role_router, role_user_router, knowledge_base_router, role_knowledge_base_router, \
    session_router, announcement_router, announcement_attachment_router, document_router, user_knowledge_base_router
from util.file_util import read_file_content, chunk_text_by_sentence

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

app.include_router(authentication.router)
app.include_router(user_router.router)
app.include_router(role_router.router)
app.include_router(role_user_router.router)
app.include_router(knowledge_base_router.router)
app.include_router(role_knowledge_base_router.router)
app.include_router(session_router.router)
app.include_router(announcement_router.router)
app.include_router(announcement_attachment_router.router)
app.include_router(document_router.router)
app.include_router(user_knowledge_base_router.router)


@app.get("/chroma/chunk_count")
async def chroma_chunk_count(knowledge_base_id: int, document_id: int):
    result = Result()

    chroma_service = ChromaService()
    chunk_count = chroma_service.get_document_chunk_count(knowledge_base_id, document_id)
    return result.success(data=chunk_count)

@app.get("/chroma/query_similar")
async def chroma_query_similar(knowledge_base_id: int, query: str):
    result = Result()

    embeddings = EmbeddingService().embed_query(query)

    chroma_service = ChromaService()
    res = chroma_service.query_similar(
        knowledge_base_id=knowledge_base_id,
        query_embedding=embeddings
    )
    return result.success(data=res)

@app.post("/upload")
async def upload_read(file: UploadFile = File(...)):
    content = await read_file_content(file)
    return content

@app.post("/upload/chunk")
async def upload_read(file: UploadFile = File(...)):
    content = await read_file_content(file)
    return chunk_text_by_sentence(content)

@app.post("/embedding")
async def embedding(file: UploadFile = File(...)):
    from model.result import Result
    result = Result()
    content = await read_file_content(file)
    chunks = chunk_text_by_sentence(content)
    from ai.embedding import EmbeddingService
    embedding_result = EmbeddingService().embed_texts(texts=chunks)
    return result.success(msg=str(len(embedding_result)), data=embedding_result)