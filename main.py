from fastapi import FastAPI

from authentication import authentication
from router import user_router, role_router, role_user_router, knowledge_base_router, role_knowledge_base_router, \
    session_router, announcement_router, announcement_attachment_router, document_router

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