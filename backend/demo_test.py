import requests
import time

# 假設這是你們建立 Job 的 API 端點 (請根據實際路由修改)
API_URL = "http://localhost:8000/api/jobs"
# 如果你們的 API 需要登入 Token，請放在這裡
HEADERS = {
    "Content-Type": "application/json",
    # "Authorization": "Bearer YOUR_ADMIN_TOKEN_HERE"
}

def create_job(payload):
    response = requests.post(API_URL, json=payload, headers=HEADERS)
    if response.status_code == 201 or response.status_code == 200:
        print(f"✅ 成功建立任務: {payload['job_name']}")
    else:
        print(f"❌ 建立失敗: {response.text}")

print("🚀 開始注入 Demo 測試任務...\\n")

# 1. 注入 10 個「單次」且「耗時」的任務
for i in range(1, 11):
    payload = {
        "job_name": f"耗時任務_Worker_Test_{i}",
        "method": "POST",
        "endpoint": "http://httpbin.org/delay/5",
        "schedule_type": "ONE_TIME",  # 👈 建議改成全大寫 (視你的 models.py 實際定義而定)
        "body": {"task_type": "http", "timeout_seconds": 10}
    }
    create_job(payload)

# 2. 注入 2 個「每分鐘執行一次」的排程任務
for i in range(1, 3):
    payload = {
        "job_name": f"每分鐘排程_Scheduler_Test_{i}",
        "method": "GET",
        "endpoint": "http://httpbin.org/get",
        "schedule_type": "RECURRING", # 👈 建議改成全大寫
        "cron_expression": "* * * * *",
        "body": {"task_type": "http"}
    }
    create_job(payload)

print("\\n🎉 測試任務注入完畢！請前往 Docker 查看 Logs。")