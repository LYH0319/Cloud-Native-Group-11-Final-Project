import redis
import json
import time
import logging
import os
import socket
import threading  # 引入線程庫，處理長任務的非同步心跳 (NFR: 長時間任務處理)
from sqlalchemy.orm import Session
from sqlalchemy.orm import scoped_session, sessionmaker

# 1. 引入系統設定
from config.setting import settings
from src.worker.schemas import TaskPayload, HeartbeatState

# 2. 引入核心執行單元（目前內部沒東西，但介面已對齊）
from src.worker.tasks.http_task import run_http_task
from src.worker.tasks.shell_task import run_shell_task

# 3. 引入 沅籈 寫好的資料庫更新函式與狀態定義
from src.database import schemas
from src.database.crud import (
    refresh_execution_heartbeat,
    report_execution_result,
    update_execution_status,
)
from src.database.models import ExecutionStatus
from src.database.core import SessionLocal, engine, ensure_schema_compatibility
from src.database.models import Base
from src.utils.logger import write_execution_log

# 設定本地日誌，落實 可觀測性 (Observability)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("WorkerExecutor")

db_session_factory = sessionmaker(bind=engine)
db_session = scoped_session(db_session_factory)


def get_worker_id() -> str:
    return os.getenv("WORKER_ID") or socket.gethostname() or "group11-worker"


# ==================================================================
#        Redis 派發邏輯(jobs.py / cron_scheduler.py需要)
# ==================================================================
# 全域只會建立一次Redis連線基礎
redis_pool = redis.ConnectionPool(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True,
)


def dispatch_task(execution_id: int, job_dict: dict, task_type: str | None = None):
    """
    【分布式派發窗口】
    不再使用本機 Thread，而是將任務序列化為 JSON，直接推入分散式快取 Redis Queue
    """
    # 1. 重用Redis連線池
    r_client = redis.Redis(connection_pool=redis_pool)

    resolved_task_type = task_type or job_dict.get("task_type") or "http"

    # 2. 封裝成 TaskPayload 格式，根據 json.loads(message_body) 需求
    task_payload = {
        "execution_id": execution_id,
        "job_id": job_dict["job_id"],
        "task_type": resolved_task_type,  # "http" 或 "shell"
        "payload": job_dict,  # 實際要執行的 method, endpoint 等
        "timeout_threshold": job_dict.get("timeout", 300),
    }

    # 3. 將字典轉成序列化JSON字典
    message_body = json.dumps(task_payload)

    # 4. RPUSH（Right Push）推入 Redis 佇列，喚醒遠端的 Worker 容器
    queue_name = settings.JOB_QUEUE_NAME
    r_client.rpush(queue_name, message_body)
    print(f" [Redis Push] 成功將Execution ID {execution_id} 派發至queue [{queue_name}]")
    return {"queued": True, "queue_name": queue_name, "task_payload": task_payload}


def get_redis_client():
    """建立 Redis 連線，作為第二期解耦的消息佇列與心跳快取基礎"""
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=True,  # 讓讀取出來的資料直接是字串，方便解析 JSON
        socket_timeout=30,  # 允許socket等待更長時間
        health_check_interval=15,  # 定期發送ping保持連線
    )


# ==========================================
#      核心心跳線程邏輯 (長任務管理)
# ==========================================
class HeartbeatThread(threading.Thread):
    """
    第二期核心功能：長時間任務管理與可觀測性 (Observability)
    這是一個背景線程，當主線程在執行可能花費數小時的長任務時，
    此線程會每隔指定秒數向 Redis 刷新生存訊號，避免被系統判定為 Worker 崩潰
    """

    def __init__(self, r_client: redis.Redis, task: TaskPayload):
        super().__init__()
        self.r_client = r_client
        self.task = task
        self.heartbeat_key = f"heartbeat:exec_{task.execution_id}"
        self._stop_event = threading.Event()  # 用於安全控制線程何時停止

    def stop(self):
        """當主任務結束時，主線程會呼叫此函式來關閉心跳監控"""
        self._stop_event.set()

    def run(self):
        logger.info(
            f"[Heartbeat] 啟動 Execution ID {self.task.execution_id} 的背景心跳發送..."
        )

        while not self._stop_event.is_set():
            try:
                # 建立符合第二期設計需求的心跳進度資料
                state = HeartbeatState(
                    job_id=self.task.job_id,
                    execution_id=self.task.execution_id,
                    status="RUNNING",
                    last_active_time=time.time(),  # 目前的 Unix 時間戳記
                    checkpoint_line=0,  # 可依實務進度擴充
                    percentage=50.0,  # 預設暫存進度
                )

                # 將心跳狀態寫入 Redis Cache，並設定過期時間（稍大於檢查間隔，防止 Worker 暴斃時狀態殘留）
                self.r_client.set(
                    self.heartbeat_key,
                    state.model_dump_json(),
                    ex=settings.HEARTBEAT_TIMEOUT,
                )
                db: Session = SessionLocal()
                try:
                    refresh_execution_heartbeat(
                        db=db,
                        execution_id=self.task.execution_id,
                        worker_id=get_worker_id(),
                    )
                finally:
                    db.close()
                logger.debug(
                    f"[Heartbeat] 已向 Cache 刷新生存訊號: {self.heartbeat_key}"
                )

            except Exception as e:
                logger.error(f"[Heartbeat Error] 發送心跳失敗: {str(e)}")

            # 每隔 settings.HEARTBEAT_INTERVAL (預設30秒) 刷新一次，若收到 stop 訊號則提早退出
            self._stop_event.wait(timeout=settings.HEARTBEAT_INTERVAL)

        logger.info(
            f"[Heartbeat] Execution ID {self.task.execution_id} 的心跳監控已安全停止。"
        )


# ==========================================
#          資料庫結果回報同步
# ==========================================
def report_to_database(
    execution_id: int,
    status: ExecutionStatus,
    error_message: str | None = None,
    log_path: str | None = None,
    log_size: int | None = None,
    duration: float | int | None = None,
    retry_count: int | None = None,
):
    """
    呼叫 沅籈 寫好的 update_execution_status 函式。
    自動處理：
    1. 狀態為 RUNNING 時自動蓋上 start_time 戳記。
    2. 狀態為 結束（SUCCESS/FAILED/TIMEOUT）時蓋上 end_time 並自動計算執行耗時 (duration)。
    """
    logger.info(
        f"[DB Sync] 正在同步狀態至資料庫 - Execution ID: {execution_id}, 狀態: {status.name}"
    )

    # 建立資料庫連線 Session
    db = db_session()
    try:
        worker_id = get_worker_id()
        if log_path is not None:
            result = report_execution_result(
                db=db,
                execution_id=execution_id,
                report=schemas.ExecutionWorkerUpdate(
                    status=status,
                    worker_id=worker_id,
                    error_message=error_message,
                    log_path=log_path,
                    log_size=log_size,
                    duration=duration,
                    retry_count=retry_count,
                ),
            )
            updated_record = result[0] if result is not None else None
        else:
            updated_record = update_execution_status(
                db=db,
                execution_id=execution_id,
                status=status,
                worker_id=worker_id,
                error_message=error_message,
            )
        
        db.commit()
        
        if updated_record and updated_record.duration is not None:
            logger.info(
                f"[DB Sync 成功] Exec ID {execution_id} 處理結束，系統自動計算耗時: {updated_record.duration} 秒"
            )

    except Exception as e:
        # NFR: 可靠性 (Reliability) - 捕捉資料庫異常，避免 Worker 核心迴圈因為 DB 波動而集體死機
        #db.rollback()
        logger.error(f"[DB Sync 異常] 寫入 MySQL 失敗: {str(e)}")
    finally:
        db_session.remove()  # 務必關閉 Session，釋放連線池資源


# ==========================================
#          任務核心分流與處理
# ==========================================
def process_task(task: TaskPayload, r_client: redis.Redis):
    """處理單個任務的核心生命週期管理"""
    logger.info(
        f"從佇列中取得任務，準備執行 - Execution ID: {task.execution_id}, Job ID: {task.job_id}"
    )

    # -------------------------------------------------------------
    # NFR 注意：一致性與冪等性 (Consistency / Idempotency)
    # 為了防止高流量下手動觸發因網路重試、或是 Scheduler 重複派發，我們在此實作分散式防重鎖
    # -------------------------------------------------------------
    idempotency_key = f"exec_active:{task.execution_id}"
    # setnx (Set if Not Exists) 確保同一個 execution_id 同一時間絕對不會被兩個 Worker 重複執行
    if not r_client.set(idempotency_key, "RUNNING", ex=task.timeout_threshold + 60):
        logger.warning(
            f"[IDEMPOTENCY] 偵測到重複派發請求！Execution ID {task.execution_id} 正在執行中，自動丟棄此重複任務。"
        )
        return

    # 1. 任務啟動：向 MySQL 回報狀態為 RUNNING (啟動計時)
    report_to_database(execution_id=task.execution_id, status=ExecutionStatus.RUNNING)

    # 2. 啟動背景心跳監控線程
    hb_thread = HeartbeatThread(r_client, task)
    hb_thread.start()

    final_status = ExecutionStatus.FAILED
    error_msg = None
    log_path = None
    log_size = None
    duration = None
    retry_count = None

    try:
        # 3. 根據 task_type 進行分流執行
        if task.task_type.lower() == "http":
            result = run_http_task(task.payload, task.timeout_threshold)
        elif task.task_type.lower() == "shell":
            result = run_shell_task(task.payload, task.timeout_threshold)
        else:
            raise ValueError(f"不支援的任務類型: {task.task_type}")

        # 4. 解析 Task 傳回的狀態，並映射到 MySQL 的 Enum
        status_map = {
            "Success": ExecutionStatus.SUCCESS,
            "Failed": ExecutionStatus.FAILED,
            "Timeout": ExecutionStatus.TIMEOUT,
        }
        final_status = status_map.get(result["status"], ExecutionStatus.FAILED)
        error_msg = result.get("error_message")
        duration = result.get("duration")
        retry_count = result.get("retry_count")
        if "log" in result and result["log"] is not None:
            log_path, log_size = write_execution_log(task.execution_id, result["log"])

    except Exception as e:
        logger.error(f"任務執行層發生未預期系統崩潰: {str(e)}")
        error_msg = f"Worker Inner Crash: {str(e)}"
        final_status = ExecutionStatus.FAILED
    finally:
        # 5. 任務不論成功、失敗或拋出異常，必須立刻通知並關閉背景心跳線程
        hb_thread.stop()
        hb_thread.join()  # 等待心跳線程安全安全退場

        # 6. 清理快取：移除暫存的防重鎖與心跳紀錄，維持快取空間乾淨
        r_client.delete(idempotency_key)
        r_client.delete(f"heartbeat:exec_{task.execution_id}")

        # 7. 任務結束：回報 MySQL 最終結果（SUCCESS/FAILED/TIMEOUT），觸發自動計算 duration 邏輯
        report_to_database(
            execution_id=task.execution_id,
            status=final_status,
            error_message=error_msg,
            log_path=log_path,
            log_size=log_size,
            duration=duration,
            retry_count=retry_count,
        )
        logger.info(f"任務處理完成，已釋放資源 - Execution ID: {task.execution_id}")


# ==========================================
#          Worker 主迴圈監聽
# ==========================================
def worker_loop():
    try:
        logger.info("[DB Init] 正在檢查定自動建立MySQL所有資料表...")
        Base.metadata.create_all(bind=engine)
        ensure_schema_compatibility(engine)
        logger.info("[DB Init 成功] MySQL 資料表確認建立完成!")
    except Exception as e:
        logger.warning(f"[DB Init 警告] 自動建表失敗，請確認連線或設定: {str(e)}")

    r_client = get_redis_client()
    queue_name = settings.JOB_QUEUE_NAME

    logger.info("Distributed Asynchronous Job Scheduler Worker Pool 已啟動。")
    logger.info(f"正在以非同步事件驅動模式監聽 Redis 佇列 [{queue_name}]...")

    while True:
        try:
            # BLPOP 是一個阻塞式左端讀取指令（Blocking Left Pop）
            # 當 Queue 裡面沒有任務時，Worker 會在此進入阻塞掛機狀態，完全不消耗 CPU 資源
            # 一旦派發端推入任務，其中一個 Worker 容器會瞬間被喚醒領走任務，落實高吞吐不遺漏保證
            task_data = r_client.blpop(queue_name, timeout=5)

            if task_data:
                # blpop 回傳格式為 tuple: (key_name, value)
                _, message_body = task_data

                # 反序列化 JSON 字串並透過 Pydantic 強型別檢查資料一致性
                raw_json = json.loads(message_body)
                task = TaskPayload(**raw_json)

                # 開始跑核心處理流程
                process_task(task, r_client)

        except json.JSONDecodeError:
            logger.error("從 Queue 中接收到無效的 JSON 字串，自動拋棄。")
        except Exception as e:
            # 防止非預期的極端異常直接讓整個 Worker Pool 容器崩潰關閉
            logger.error(f"Worker Loop 內部發生未預期異常: {str(e)}")
            time.sleep(2)  # 暫停 2 秒，避免極端狀況下衝爆無窮迴圈


if __name__ == "__main__":
    worker_loop()
