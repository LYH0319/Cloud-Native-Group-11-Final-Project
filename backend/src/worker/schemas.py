from pydantic import BaseModel, Field
from typing import Dict, Optional, Any

# ==========================================
# 1. 任務派發資料格式 (Message Queue Payload)
# ==========================================
class TaskPayload(BaseModel):
    """
    定義從 Redis Message Queue 中讀取出來的任務格式。
    這必須與「任務派發」端丟入的格式完全一致。
    丟入格式:
    {
        "execution_id": 1,
        "job_id": 101,
        "task_type": "http",
        "payload": {
            "method": "POST",
            "endpoint": "https://api.example.com/v1/data",
            "headers": {"Content-Type": "application/json"},
            "body": {\"name\": \"test\"}"
        },
        "timeout_threshold": 120
    }
    """
    execution_id: int = Field(..., description="對應 MySQL Executions 表的唯一識別碼 ")
    job_id: int = Field(..., description="對應 MySQL Jobs 表的唯一識別碼")
    task_type: str = Field(..., description="任務類型，例如: 'http' 或 'shell'")
    
    # 執行內容細節 (包含 REST API 的 method, endpoint, headers, body 等)
    payload: Dict[str, Any] = Field(default_factory=dict)
    
    # 時間限制設定
    timeout_threshold: int = Field(default=60, description="長時間任務的超時判定門檻 (秒)")


# ==========================================
# 2. 長時間任務心跳格式 (Redis Heartbeat State)
# ==========================================
class HeartbeatState(BaseModel):
    """
    第二期核心 NFR: 可觀測性 (Observability) 
    長時間任務管理：Worker 執行任務時會定期更新此進度並儲存在 Cache (Redis)
    """
    job_id: int
    execution_id: int
    status: str = "RUNNING"
    last_active_time: float = Field(..., description="當前的 Unix 時間戳記，供 Monitor 判定是否卡死")
    checkpoint_line: int = Field(default=0, description="目前執行到日誌的第幾行 (用於 Shell 任務等)")
    percentage: float = Field(default=0.0, description="任務執行進度百分比 (0.0 ~ 100.0)")