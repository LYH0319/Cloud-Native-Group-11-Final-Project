from sqlalchemy import select
from database import engine, SessionLocal, Base, init_db
from models import User, UserRole, Job, JobStatus, HttpMethod, JobDependency

def test_users(session):
    print("\n[階段一] 測試 User 新增與查詢...")
    # 注意這裡改成字串 "104111"
    existing_user = session.scalars(select(User).where(User.employee_id == "104111")).first()

    if existing_user:
        print("⚠️ User 資料已經存在，跳過新增。")
        user = existing_user
    else:
        user = User(employee_id="104111", username="test_dev_02", role=UserRole.DEVELOPER)
        session.add(user)
        session.flush() # 用 flush 讓資料庫先發配 user_id 給這個 user，但還沒完全 commit
        print("✅ 成功新增 User！")
    
    print(f"--- 目前使用的 User: {user} ---")
    return user

def test_jobs(session, user):
    print("\n[階段二] 測試 Job 與 JobDependency 新增與查詢...")
    
    # 檢查是否已經有這個使用者的 Job，避免重複新增
    existing_jobs = session.scalars(select(Job).where(Job.owner_id == user.user_id)).all()
    
    if existing_jobs:
        print("⚠️ 該 User 的 Job 資料已經存在，跳過新增。")
    else:
        # 1. 建立上游任務 (例如：抓取資料)
        upstream_job = Job(
            owner_id=user.user_id,
            job_name="Fetch Data Job",
            method=HttpMethod.GET,
            endpoint="https://api.example.com/data",
            status=JobStatus.ACTIVE,
            has_dependency=False
        )
        
        # 2. 建立下游任務 (例如：處理資料)
        downstream_job = Job(
            owner_id=user.user_id,
            job_name="Process Data Job",
            method=HttpMethod.POST,
            endpoint="https://api.example.com/process",
            status=JobStatus.ACTIVE,
            has_dependency=True # 這個任務有依賴
        )
        
        # 將任務加入 session 並 flush 取得 job_id
        session.add_all([upstream_job, downstream_job])
        session.flush() 

        # 3. 建立相依性 (Process Data 依賴於 Fetch Data)
        dependency = JobDependency(
            upstream_id=upstream_job.job_id,
            downstream_id=downstream_job.job_id
        )
        session.add(dependency)
        print("✅ 成功新增兩個 Job 以及它們的相依性！")

    # 4. 查詢並印出結果
    print("\n--- 🎉 查詢結果 ---")
    jobs = session.scalars(select(Job).where(Job.owner_id == user.user_id)).all()
    for job in jobs:
        print(job) # 這裡會呼叫你寫的 __repr__
        
        # 如果這個任務有「上游任務」(代表它在等別人)
        if job.upstream_dependencies:
            for dep in job.upstream_dependencies:
                # 透過 relationship 直接印出它依賴的任務名稱
                print(f"   ↳ ⚠️ 等待上游任務: {dep.upstream_job.job_name} (ID: {dep.upstream_id})")
        
        # 如果這個任務有「下游任務」(代表別人在等它)
        if job.downstream_dependencies:
            for dep in job.downstream_dependencies:
                print(f"   ↳ 🚀 觸發下游任務: {dep.downstream_job.job_name} (ID: {dep.downstream_id})")

def run_test():
    init_db()

    with SessionLocal.begin() as session:
        # 取得 User
        user = test_users(session)
        # 把 User 傳遞給 Job 測試函數
        test_jobs(session, user)
        # 離開 with 區塊時會自動 commit 所有的變更

if __name__ == "__main__":
    run_test()