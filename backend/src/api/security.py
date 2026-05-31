from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """將明文密碼加密成雜湊碼"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """驗證明文密碼與資料庫的雜湊碼是否相符"""
    return pwd_context.verify(plain_password, hashed_password)