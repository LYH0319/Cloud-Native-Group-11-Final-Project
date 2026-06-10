from pydantic import BaseModel


# 1. 檢查 ID
class CheckIdRequest(BaseModel):
    employee_id: str


class CheckIdResponse(BaseModel):
    isRegistered: bool


# 2. 註冊密碼
class RegisterPasswordRequest(BaseModel):
    employee_id: str
    password: str


# 3. 登入驗證
class LoginRequest(BaseModel):
    employee_id: str
    password: str


class LoginResponse(BaseModel):
    id: str  # 對應前端的 user.id (通常放 employee_id)
    role: str  # 'developer' | 'operator' | 'admin'


# 4. 重設密碼
class ResetPasswordRequest(BaseModel):
    employee_id: str
    new_password: str
