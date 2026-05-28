from sqlalchemy import select
from database import engine, SessionLocal, Base, init_db
from models import User, UserRole, Job, JobStatus, HttpMethod, JobDependency, ScheduleType, Execution, ExecutionStatus, TriggerType, LogReference
from datetime import datetime

def test_users(session):
    print("\n[階段一] 測試 User 新增與查詢...")
    existing_user = session.scalars(select(User).where(User.employee_id == "104111")).first()

    if existing_user:
        print("⚠️ User 資料已經存在，跳過新增。")
        user = existing_user
    else:
        user = User(employee_id="104111", username="test_dev_02", role=UserRole.DEVELOPER)
        session.add(user)
        session.flush() 
        print("✅ 成功新增 User！")
    
    print(f"--- 目前使用的 User: {user} ---")
    return user

def test_jobs_and_infrastructure(session, user):
    print("\n[階段二] 測試完整排程、執行紀錄與日誌鏈結...")
    
    # 檢查是否已有該使用者的 Job 
    existing_job = session.scalars(select(Job).where(Job.owner_id == user.user_id)).first()
    
    if existing_job:
        print("⚠️ 該 User 的 Job 資料已存在，跳過後續新增步驟。")
        # 為了展示查詢，我們直接拿既有的資料來跑階段三
    else:
        # 1. 建立一個週期性排程任務
        cron_job = Job(
            owner_id=user.user_id,
            job_name="Hourly Sync Job",
            method=HttpMethod.GET,
            endpoint="https://api.example.com/sync",
            status=JobStatus.ACTIVE,
            has_dependency=False,
            schedule_type=ScheduleType.RECURRING,
            cron_expression="0 * * * *"  # 每小時執行
        )
        session.add(cron_job)
        session.flush()

        # 2. 模擬 Scheduler 觸發了一次任務，建立 Execution 紀錄
        execution_record = Execution(
            job_id=cron_job.job_id,
            trigger_type=TriggerType.SCHEDULER,
            status=ExecutionStatus.SUCCESS, # 假設這跑成功了
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=2, # 耗時 2 秒
            worker_id="k8s-worker-node-01"
        )
        session.add(execution_record)
        session.flush()

        # 3. 模擬 Worker 執行成功後，上傳並關聯 Log 檔案位置
        log_file = LogReference(
            execution_id=execution_record.execution_id,
            log_path="s3://cloud-native-logs/2026/05/exec_01.log",
            log_size=4096 # 4 KB
        )
        session.add(log_file)
        print("✅ 成功建立 Job ➜ Execution ➜ LogReference 完整鏈結！")

    # --- [階段三] 驗證強大的 ORM 跨表撈取能力 ---
    print("\n--- 🎉 系統完整資料鏈深度查詢 ---")
    jobs = session.scalars(select(Job).where(Job.owner_id == user.user_id)).all()
    
    for job in jobs:
        print(f"\n任務名稱: {job.job_name} [{job.schedule_type.value}] (Cron: {job.cron_expression})")
        
        if job.executions:
            print(f"  ↳ 📊 共有 {len(job.executions)} 次執行紀錄：")
            for exec_data in job.executions:
                print(f"    - 執行 ID: {exec_data.execution_id} | 狀態: {exec_data.status.name} | 耗時: {exec_data.duration}s")
                
                # 直接透過 relationship 一路泡茶摸到 Log 資料！
                if exec_data.log_reference:
                    print(f"      - 📝 關聯日誌位置: {exec_data.log_reference.log_path} ({exec_data.log_reference.log_size} Bytes)")
                else:
                    print("      - 📝 此執行紀錄尚無日誌。")
        else:
            print("  ↳ 📊 該任務目前尚無執行紀錄。")

def run_test():
    init_db()
    with SessionLocal.begin() as session:
        user = test_users(session)
        test_jobs_and_infrastructure(session, user)

if __name__ == "__main__":
    run_test()