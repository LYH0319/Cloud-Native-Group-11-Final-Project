import pytest
import json
import redis
import time
from unittest.mock import MagicMock, patch
from src.worker.schemas import TaskPayload
from src.worker.executor import process_task
from src.database.models import ExecutionStatus
from src.worker.executor import check_task_timeout

@pytest.fixture
def mock_redis():
    """模擬 Redis 用戶端"""
    client = MagicMock(spec=redis.Redis)
    # 預設讓 setnx 成功回傳 True (代表未重複派發)
    client.set.return_value = True
    return client

@pytest.fixture
def sample_task():
    """建立一個符合強型別規格的測試任務資料"""
    return TaskPayload(
        execution_id=8888,
        job_id=99,
        task_type="http",
        payload={
            "method": "GET",
            "endpoint": "https://httpbin.org/get"
        },
        timeout_threshold=10
    )

# -------------------------------------------------------------
# 測試案例 1：驗證 Worker 能否正常執行完成，並正確呼叫資料庫同步
# -------------------------------------------------------------
@patch("src.worker.executor.report_to_database")
@patch("src.worker.executor.run_http_task")
def test_process_task_success(mock_run_http, mock_report_db, sample_task, mock_redis):
    # 模擬 HTTP 執行器回傳成功的字典
    mock_run_http.return_value = {
        "status": "Success",
        "duration": 1.5,
        "error_message": "",
        "log": "HTTP SUCCESS LOG"
    }

    # 執行你要測試的目標函式
    process_task(sample_task, mock_redis)

    # 驗證 1：任務開始時，必須向資料庫回報為 RUNNING 狀態
    mock_report_db.assert_any_call(execution_id=8888, status=ExecutionStatus.RUNNING)

    # 驗證 2：任務結束時，必須根據回傳狀態向資料庫回報為 SUCCESS 狀態
    mock_report_db.assert_any_call(execution_id=8888, status=ExecutionStatus.SUCCESS, error_message="")

    # 驗證 3：任務結束後，必須確實把 Redis 內部的防重鎖與心跳刪除，維持快取乾淨
    mock_redis.delete.assert_any_call("exec_active:8888")
    mock_redis.delete.assert_any_call("heartbeat:exec_8888")


# -------------------------------------------------------------
# 測試案例 2：驗證防重鎖（Idempotency NFR）是否能阻擋重複執行的請求
# -------------------------------------------------------------
@patch("src.worker.executor.report_to_database")
def test_process_task_idempotency_blocked(mock_report_db, sample_task, mock_redis):
    # 關鍵設定：讓 Redis 的 set nx 傳回 False，代表這個任務已經有人在跑了，鎖被佔用
    mock_redis.set.return_value = False

    # 執行目標函式
    process_task(sample_task, mock_redis)

    # 驗證：既然被防重鎖擋掉，程式必須立刻 return，絕對不能呼叫資料庫回報 RUNNING！
    mock_report_db.assert_not_called()
    
# -------------------------------------------------------------
# 測試案例 3 :驗證長時間任務，當任務超過他自己設定的threshold後要回報錯誤
# -------------------------------------------------------------
def test_task_timeout_logic():
    # 1. 建立一個假的任務，設定超時門檻為 30 秒
    fake_task = MagicMock()
    fake_task.start_time = 1000.0  # 假設開始時間戳記是 1000
    fake_task.timeout_threshold = 30
    
    # 2. 利用 patch 劫持 time.time()
    # 第一次呼叫回傳 1010（只過 10 秒 -> 應該沒超時）
    # 第二次呼叫回傳 1040（過了 40 秒 -> 應該要觸發超時！）
    with patch("src.worker.executor.time.time", side_effect=[1010.0, 1040.0]):
        
        # 第一次檢查：才過 10 秒，預期回傳 False (未超時)
        assert check_task_timeout(fake_task) is False
        
        # 第二次檢查：時間被我們快進到了 40 秒，預期回傳 True (已超時)
        assert check_task_timeout(fake_task) is True