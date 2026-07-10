from fastapi import FastAPI

from authentication import authentication
from router import user_router, role_router

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

app.include_router(authentication.router)
app.include_router(user_router.router)
app.include_router(role_router.router)