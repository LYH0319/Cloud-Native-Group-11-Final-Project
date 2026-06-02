from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database.core import get_db # 請替換為你實際的 get_db 引入路徑
import src.database.schemas as schemas
import src.database.crud as crud

# 假設你有一個 security 模組負責密碼的 Hash 處理
# 如果沒有，請參考 crud.py 中原本引用 hash_password 的來源
from src.api.security import hash_password 

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)

@router.post("/check-id")
def check_id(request: schemas.CheckIdRequest, db: Session = Depends(get_db)):
    """
    檢查員工編號是否存在，以及是否已經設定過密碼
    """
    user = crud.get_user_by_employee_id(db, employee_id=request.employee_id)
    
    if not user:
        # 前端預期接到 404 來觸發 "查無此員工編號" 錯誤
        raise HTTPException(status_code=404, detail="Can not find ID")
    
    # 判斷是否註冊過密碼 (假設以 hashed_password 欄位是否有值來判定)
    is_registered = bool(user.hashed_password)
    
    return {"isRegistered": is_registered}


@router.post("/register-password")
def register_password(request: schemas.PasswordRequest, db: Session = Depends(get_db)):
    """
    初次設定密碼
    """
    user = crud.get_user_by_employee_id(db, employee_id=request.employee_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="Can not find ID")
        
    if user.hashed_password:
        raise HTTPException(status_code=400, detail="Password already registered")

    # 將密碼 Hash 後存入資料庫
    user.hashed_password = hash_password(request.password)
    db.commit()
    
    return {"message": "Password registered successfully"}


@router.post("/login-password", response_model=schemas.UserResponse)
def login_password(request: schemas.PasswordRequest, db: Session = Depends(get_db)):
    """
    驗證登入並回傳 User 資訊 (前端會存入 localStorage)
    """
    # crud.py 裡面已經有 authenticate_user 可以直接用
    user = crud.authenticate_user(db, identifier=request.employee_id, password=request.password)
    
    if not user:
        # 前端攔截 'Password incorrect' 的 Error，所以回傳 401 或 400 皆可
        raise HTTPException(status_code=401, detail="Password incorrect")
        
    return user


@router.post("/reset-password")
def reset_password(request: schemas.ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    重設密碼
    """
    user = crud.get_user_by_employee_id(db, employee_id=request.employee_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="Can not find ID")

    # 將新密碼 Hash 後更新
    user.hashed_password = hash_password(request.new_password)
    db.commit()
    
    return {"message": "Password reset successfully"}