from sqlalchemy import select
from database import engine, SessionLocal, Base, init_db
from models import User, UserRole  # 把你的藍圖引入進來

def run_test():
    # 1. 根據模型在 MySQL 建立真實的 Table
    init_db()

    # 2. 測試新增資料
    with SessionLocal.begin() as session:
        # 先去資料庫找找看，是不是已經有這個員編了？
        existing_user = session.scalars(
            select(User).where(User.employee_id == 104111)
        ).first()

        if existing_user:
            print("⚠️ 測試資料已經存在，跳過新增步驟。")
        else:
            # 如果沒有找到，才建立新的 User
            new_user = User(
                employee_id=104111,
                username="test_dev_02",
                role=UserRole.DEVELOPER
            )
            session.add(new_user)
            print("✅ 成功新增 User！")

    # 3. 開新 Session 查詢所有的資料
    with SessionLocal() as session:
        # 將 .first() 改成 .all()，變數名稱習慣上會加上 s (users)
        users = session.scalars(select(User)).all()
        
        if users:
            print(f"\n--- 🎉 成功從資料庫撈出 {len(users)} 筆 User 資訊 ---")
            
            # 使用 for 迴圈把每一個 user 印出來
            for user in users:
                print(f"ID: {user.user_id}")
                print(f"員編: {user.employee_id}")
                print(f"名稱: {user.username}")
                print(f"角色: {user.role.value}")  
                print(f"建立時間: {user.created_at}")
                print(f"更新時間: {user.updated_at}")
                print("-" * 30)  # 印出一條分隔線區隔每個人
        else:
            print("目前資料庫裡面沒有任何 User 資料喔！")

if __name__ == "__main__":
    run_test()