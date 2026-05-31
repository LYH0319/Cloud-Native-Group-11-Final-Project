from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # Database Settings
    DATABASE_URL: str = Field(default="sqlite:///./test.db")

    # Redis Settings (第二期核心：MQ 與 Heartbeat 快取)
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    
    # 隊列與心跳設定
    JOB_QUEUE_NAME: str = "job_priority_queue"  # 第二期升級為 Priority 概念或基本 Queue
    HEARTBEAT_INTERVAL: int = 30  # Worker 每 30 秒回報一次心跳
    HEARTBEAT_TIMEOUT: int = 60   # 超過 60 秒未更新視為超時崩潰

    #class Config:
    #    env_file = ".env"
    #    extra = "ignore"

    model_config = SettingsConfigDict(
        env_file=".env.local",      # 優先讀取 .env.local 檔案（給本地 pytest 測試連 MySQL）
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()