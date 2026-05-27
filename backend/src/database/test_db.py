# backend/test_db.py
from sqlalchemy import create_engine, text

# 測試用連線字串 (注意：這裡故意把 db 改成 localhost，因為我們從本機外面連進去)
# 請把帳號密碼換成你 .env 裡面設定的 MYSQL_USER 和 MYSQL_PASSWORD
TEST_DATABASE_URL = "mysql+pymysql://api_worker:PASSWORD_group11@localhost:3306/job_scheduler"

print("🔄 正在嘗試連線到 MySQL...")

try:
    # 建立引擎 (水管)
    engine = create_engine(TEST_DATABASE_URL)
    
    # 建立一次性連線並發送最簡單的 SQL 查詢
    with engine.connect() as conn:
        # text() 是用來包裝原生 SQL 語法的工具
        result = conn.execute(text("SELECT VERSION();"))
        db_version = result.scalar() # 取出第一筆結果
        
        print("=====================================")
        print("🎉 敲門成功！資料庫活著！")
        print(f"📌 MySQL 版本: {db_version}")
        print("=====================================")

except Exception as e:
    print("=====================================")
    print("崩潰！連線失敗 QAQ")
    print(f"錯誤訊息: {e}")
    print("=====================================")