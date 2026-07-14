from fastapi import FastAPI, UploadFile, File

from authentication import authentication
from router import user_router, role_router, role_user_router, knowledge_base_router, role_knowledge_base_router, \
    session_router, announcement_router, announcement_attachment_router, document_router
from util.file_util import read_file_content

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

@app.post("/upload")
async def upload_read(file: UploadFile = File(...)):
    content = await read_file_content(file)
    return content