from passlib.context import CryptContext

# 建立密碼加密上下文，指定使用 bcrypt 演算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    將明文密碼進行 Hash 加密
    
    Args:
        password (str): 原始明文密碼
        
    Returns:
        str: 加密後的 Hash 字串
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    驗證明文密碼與資料庫中的 Hash 密碼是否相符
    
    Args:
        plain_password (str): 使用者輸入的明文密碼
        hashed_password (str): 資料庫中儲存的 Hash 密碼
        
    Returns:
        bool: 密碼正確回傳 True，錯誤回傳 False
    """
    return pwd_context.verify(plain_password, hashed_password)