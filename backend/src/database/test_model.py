from sqlalchemy import select
from database import engine, SessionLocal, Base, init_db
from models import User, UserRole  # 把你的藍圖引入進來

def run_test():
    # 1. 根據模型在 MySQL 建立真實的 Table
    init_db()

    # 2. 測試新增資料
    with SessionLocal.begin() as session:
        # 建立一個測試用的 User (注意：不需要填 created_at 和 updated_at，資料庫會搞定)
        new_user = User(
            employee_id=104123,
            username="test_dev_01",
            role=UserRole.DEVELOPER
        )
        
        session.add(new_user)
        print("成功新增 User(離開 with 區塊時會自動 commit)")

    # 3. 開新 Session 查詢剛剛新增的資料
    with SessionLocal() as session:
        # 查詢第一筆 User
        user = session.scalars(select(User)).first()
        
        if user:
            print("\n--- 🎉 成功從資料庫撈出 User 資訊 ---")
            print(f"ID: {user.user_id}")
            print(f"員編: {user.employee_id}")
            print(f"名稱: {user.username}")
            print(f"角色: {user.role.value}")  # Enum 取值要用 .value
            print(f"建立時間: {user.created_at}")
            print(f"更新時間: {user.updated_at}")

if __name__ == "__main__":
    run_test()