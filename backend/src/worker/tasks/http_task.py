import time


def run_http_task(payload, timeout_threshold):
    logger_msg = "開始模擬長時間任務..."
    print("[Task] 收到任務，正在模擬耗時長任務，阻斷10s")
    time.sleep(10)  # 模擬任務執行時間

    return {
        "status": "Success",
        "duration": 10.0,
        "error_message": "",
        "log": "MOCK LONG HTTP TASK SUCCESS",
    }
