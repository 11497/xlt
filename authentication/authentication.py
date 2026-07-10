from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from config.jwt_config import JWT_CONFIG
from crud.user_crud import UserCRUD
from util.jwt_util import JwtUtil

jwt_util = JwtUtil(secret_key=JWT_CONFIG["secret_key"], algorithm=JWT_CONFIG["algorithm"],
                   access_token_expire_minutes=JWT_CONFIG["access_token_expire_minutes"])

router = APIRouter(prefix="/api", tags=["authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth")
def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    依赖项：自动从 Authorization: Bearer xxx 中提取 token
    如果请求头缺失或格式不对，FastAPI 会自动返回 401
    """
    payload = jwt_util.verify_token(token, expected_type="access")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload

@router.post("/auth")
async def auth(form_data: OAuth2PasswordRequestForm = Depends()):
    """Swagger 认证接口"""
    login_user = UserCRUD.get_by_username(form_data.username)
    if login_user.password != form_data.password:
        return HTTPException(status_code=401, detail="密码错误")

    token = jwt_util.create_access_token(data={"user_id": login_user.id})
    return {"access_token": token, "token_type": "bearer"}