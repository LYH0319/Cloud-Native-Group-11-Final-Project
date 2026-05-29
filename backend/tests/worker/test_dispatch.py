# backend/test_dispatch.py
import redis
import json


def send_test_tasks():
    # 建立與本地 Docker Redis 的連線
    # (因為你在本機執行腳本連 Docker，host 填 'localhost'，Port 6379 已經對外映射)
    r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
    queue_name = "job_priority_queue"

    # -------------------------------------------------------------
    # 測試案例 1：標準 HTTP 長任務（測試任務執行 + 長時間心跳續命）
    # -------------------------------------------------------------
    http_task = {
        "execution_id": 1001,  # 模擬 MySQL 中的執行紀錄 ID [cite: 19, 243]
        "job_id": 42,  # 模擬 Job ID [cite: 19, 210]
        "task_type": "http",  # 觸發 HTTP 執行器
        "payload": {
            "method": "GET",
            "endpoint": "https://httpbin.org/delay/10",  # 這個網址會故意卡住 10 秒才回傳，絕佳的長任務測試點！
            "headers": {"Accept": "application/json"},
            "body": {},
        },
        "timeout_threshold": 30,  # 設定 30 秒超時限制 [cite: 7, 27]
    }

    # 序列化並推入隊列 (模擬蔡佳倩負責的任務派發端)
    r.rpush(queue_name, json.dumps(http_task))
    print(f"🚀 [已派發任務 1] 10秒長任務已塞入 Redis Queue: {queue_name}")

    # -------------------------------------------------------------
    # 測試案例 2：冪等性測試（測試手動重複觸發是否會被防重鎖擋掉）
    # -------------------------------------------------------------
    # 我們複製一個一模一樣 execution_id 的任務緊跟在後推入
    duplicate_task = http_task.copy()
    r.rpush(queue_name, json.dumps(duplicate_task))
    print(f"🛡️ [已派發任務 2] 故意推入相同 Execution ID 的重複請求進行防重測試...")


if __name__ == "__main__":
    send_test_tasks()
