# backend/mock_dispatch.py
import redis
import json
import time


def trigger_mock_job():
    # 連線到本地的 Redis (如果你是用 docker 跑，localhost 要對應好 ports)
    r = redis.Redis(host="localhost", port=6379, db=0)

    # 模擬佳倩那邊會丟進來的任務資料 (嚴格符合你的 TaskPayload)
    mock_task = {
        "execution_id": 999,  # 模擬 MySQL 裡的執行紀錄 ID
        "job_id": 42,  # 模擬 Job ID
        "task_type": "http",  # 測試 HTTP Task
        "payload": {
            "method": "GET",
            "endpoint": "https://httpbin.org/delay/2",  # 這個網址會故意延遲 2 秒回傳，很適合測試長任務與心跳！
            "headers": {"Accept": "application/json"},
            "body": {},
        },
        "timeout_threshold": 10,  # 10 秒超時門檻
    }

    # 將字典轉換成 JSON 字串
    task_json = json.dumps(mock_task)

    # 丟進 Redis 的 List 中 (這就是你們的 Message Queue)
    # 這裡用 rpush 代表從右邊塞入，你的 Worker 就會從左邊 blpop 取出 (先進先出 FIFO)
    queue_name = "job_priority_queue"
    r.rpush(queue_name, task_json)

    print(f"成功派發模擬任務！已塞入 Redis Queue [{queue_name}]")
    print(f"資料內容: {task_json}")


if __name__ == "__main__":
    # 執行前確保你的 docker-compose 中的 redis 已經啟動了喔！
    trigger_mock_job()
