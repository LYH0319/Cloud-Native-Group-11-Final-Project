from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# 引入剛才建立的 schemas 與 security，以及你原本的 db, crud
import src.database.crud as crud
import src.database.schemas as schemas
from src.api import security
from src.database.connection import get_db

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)

# 1. 檢查員工編號是否存在與是否已註冊密碼
@router.post("/check-id", response_model=schemas.CheckIdResponse)
def check_id(payload: schemas.CheckIdRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_employee_id(db, employee_id=payload.employee_id)
    
    # 如果找不到該員工，拋出 404，前端會觸發 "查無此員工編號"
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Can not find ID"
        )
    
    # 判斷該員工是否已經設定過密碼 (假設 User 模型有 hashed_password 欄位)
    is_registered = True if getattr(user, "hashed_password", None) else False
    
    return {"isRegistered": is_registered}


# 2. 註冊新密碼
@router.post("/register-password")
def register_password(payload: schemas.RegisterPasswordRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_employee_id(db, employee_id=payload.employee_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # 檢查是否已經註冊過，防止重複註冊覆蓋
    if getattr(user, "hashed_password", None):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password already registered")
    
    # 加密密碼並寫入資料庫
    user.hashed_password = security.get_password_hash(payload.password)
    db.commit()
    
    return {"message": "Registration successful"}


# 3. 登入驗證
@router.post("/login-password", response_model=schemas.LoginResponse)
def login_password(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_employee_id(db, employee_id=payload.employee_id)
    
    # 找不到使用者，或者密碼尚未設定
    if not user or not getattr(user, "hashed_password", None):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Password incorrect"
        )
    
    # 驗證密碼是否正確
    if not security.verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Password incorrect"
        )
    
    # 登入成功，回傳符合前端 User 型態的資料
    return {
        "id": user.employee_id,
        "role": user.role # 這裡的 user.role 必須是 'developer', 'operator', 或 'admin'
    }


# 4. 重設密碼 (忘記密碼)
@router.post("/reset-password")
def reset_password(payload: schemas.ResetPasswordRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_employee_id(db, employee_id=payload.employee_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # 覆蓋舊密碼
    user.hashed_password = security.get_password_hash(payload.new_password)
    db.commit()
    
    return {"message": "Reset password successful"}