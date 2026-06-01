# Cloud-Native-Group-11-Final-Project

## 👥 小組分工 (Team & Responsibilities)
| 姓名 / GitHub | 學號 | 主要負責模組 / 職責 |
| :--- | :--- | :--- |
| **謝羽媞** (@yosoramagician) | 112062315 | 前端 UI 介面設計、使用者註冊 / 登入、Job 管理 |
| **李沅籈** (@stellae2718) | 112062207 | CI/CD、排程規則設定、資料庫設定 |
| **謝絜淩** (@Chiehling0214) | 112062220 | 執行結果回報、執行歷史查詢、手動觸發 |
| **廖宇嬅** (@LYH0319) | 112062301 | 任務執行、長時間任務處理 |
| **蔡佳倩** (@chien1201) | 112062308 | 任務派發、任務相依性管理、Job 註冊 |

## 🛠️ CI/CD 本地測試指南 (Local CI/CD Testing)

目前 CI 包含兩個測試流程。

### ci-frontend
- on:
  - push with changes in frontend/
  - pull request
- including:
  - typecheck
  - prettier check
  - test & test report

### ci-backend
- on:
  - push with changes in backend/
  - pull request
- including:
  - flake8
  - pytest

### cd
目前只是初步範例，尚未完整測試。

- on:
  - push to release/ branch

### local ci test
1. 確保電腦已安裝並啟動 **Docker Desktop**
2. 安裝 `act` 工具
3. 執行本地測試命令：

    ```bash
    # 模擬 Git Push 事件，完整跑一遍前後端 CI 流程
    act push

    # 單獨測試前端或後端 workflow
    act -W .github/workflows/ci-frontend.yaml
    act -W .github/workflows/ci-backend.yaml
    ```

4. local ci test 如果 fail 在 `Test report` 是正常的，可以直接 push。

### backend test
後端測試已依照測試類型拆成 `unit` 與 `integration`，也可以用 pytest marker 分開執行。

```bash
cd backend

# 跑全部 backend tests：auth、job、execution、scheduler、worker、CRUD、utils
pytest

# 只跑 unit tests：單一模組或單一層級邏輯，外部服務以 fixture/mock 隔離
pytest -m unit

# 只跑 integration tests：API + DB、scheduler + dispatch、worker + execution flow
pytest -m integration

# 排除 integration tests：快速檢查大多數純邏輯與資料層測試
pytest -m "not integration"

# 直接指定 unit 測試資料夾：等同集中跑單元測試檔
pytest tests/unit

# 直接指定 integration 測試資料夾：等同集中跑整合流程測試檔
pytest tests/integration

# CI 使用的語法級 flake8 檢查：只檢查會造成執行失敗的錯誤類型
python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
```

## 🛠️ database CRUD 使用指南

目前已完成 User、Job、Execution、JobDependency、LogReference 相關 CRUD 功能。
若需使用，請直接從 `src.database.crud` 引入對應函式。

### 使用建議
- 請務必將 `db: Session` 作為第一個參數傳入。
- 涉及狀態變更的操作，請優先使用商業邏輯導向的函式，例如 `change_job_status()`、`update_execution_status()`、`report_execution_result()`。
- Scheduler 與 Worker 應直接使用 database/service/CRUD 函式，不需要透過 HTTP API 更新內部狀態。
- 若需新增測試，請參考 `backend/tests/` 內既有測試的 Arrange-Act-Assert 結構。

### 新增功能
如果要請求新增 CRUD 功能，請複製並填寫以下內容：

```text
功能名稱：（例如：查詢某個時間區間內的執行紀錄）
目標資料表：（例如：Execution）
參數需求：（需要輸入什麼資料？回傳什麼結果？）
商業邏輯：（是否有特殊的篩選條件或狀態轉換？）
優先級：（High / Medium / Low）
```

## 📂 專案開發目錄架構 Project Directory Structure

本專案採前後端分離架構，後端以 FastAPI、MySQL、Redis、Scheduler、Worker 組成完整任務排程與執行流程；前端資料夾包含正式前端與一個開發測試用的單檔模擬前端。

```text
Cloud-Native-Group-11-Final-Project/
│
├── .github/                         # GitHub Actions CI/CD 設定
│   └── workflows/
│       ├── ci-frontend.yaml
│       ├── ci-backend.yaml
│       └── cd.yaml
│
├── docker-compose.yml               # 本地一鍵啟動 frontend/backend/db/redis/worker/scheduler
├── README.md                        # 專案說明與啟動方式
├── CONTRIBUTING.md                  # 協作規範
├── logs/                            # Worker 執行日誌掛載目錄
│
├── frontend/                        # TypeScript / Vite 前端
│   ├── Dockerfile
│   ├── package.json
│   ├── package-lock.json
│   ├── index.html
│   ├── backend-flow-test.html       # 開發測試用模擬前端，可測 auth/job/trigger/history/logs
│   ├── public/
│   │   ├── favicon.svg
│   │   └── icons.svg
│   ├── src/
│   │   ├── main.ts
│   │   ├── style.css
│   │   ├── counter.ts
│   │   └── assets/
│   └── tests/
│       └── test_dummy.test.ts
│
└── backend/                         # Python / FastAPI 後端
    ├── Dockerfile                   # FastAPI API service image
    ├── Dockerfile.worker            # Worker / Scheduler service image
    ├── requirements.txt
    ├── pytest.ini
    ├── config/
    │   └── settings.py              # 環境變數與全域設定
    │
    ├── src/
    │   ├── api/
    │   │   ├── main.py              # FastAPI app、CORS、router 掛載、DB schema compatibility
    │   │   ├── dependencies.py      # JWT current user dependency
    │   │   └── routers/
    │   │       ├── auth.py          # POST /api/auth/register、POST /api/auth/login
    │   │       ├── jobs.py          # Job 建立、列表、詳情、手動觸發，含 owner 權限檢查
    │   │       └── history.py       # Execution history、execution detail、logs 查詢
    │   │
    │   ├── database/
    │   │   ├── core.py              # SQLAlchemy engine/session/init_db/schema compatibility
    │   │   ├── connection.py        # database package 對外相容匯出
    │   │   ├── models.py            # User、Job、Execution、JobDependency、LogReference
    │   │   ├── schemas.py           # Pydantic API schemas
    │   │   └── crud.py              # User/job/execution/dependency/log CRUD 與 business helpers
    │   │
    │   ├── scheduler/
    │   │   └── cron_scheduler.py    # 定期掃描 DB，派發到期任務到 Redis
    │   │
    │   ├── worker/
    │   │   ├── queue_manager.py     # Redis queue 操作
    │   │   ├── executor.py          # Worker dispatch 與執行流程
    │   │   ├── schemas.py           # Worker task schemas
    │   │   └── tasks/
    │   │       ├── http_task.py     # HTTP 任務執行
    │   │       └── shell_task.py    # Shell 任務執行
    │   │
    │   └── utils/
    │       ├── cycle_detection.py   # Job dependency DAG cycle detection
    │       ├── logger.py            # Execution log 寫入與讀取
    │       └── security.py          # 密碼雜湊、JWT 建立與驗證
    │
    └── tests/
        ├── conftest.py              # 共用 pytest fixtures，建立隔離測試 DB session
        ├── unit/                    # 單一模組或單一層級測試
        │   ├── test_auth_dependencies.py # JWT current user dependency 與無效 token/停用使用者
        │   ├── test_cycle_detection.py   # Job dependency DAG cycle detection
        │   ├── test_database_crud.py     # User/job/execution/dependency/log CRUD 與 business helpers
        │   ├── test_database_schemas.py  # Pydantic schema validation edge cases
        │   ├── test_dummy.py             # CI smoke test
        │   ├── test_http_task.py         # HTTP task success/failure/timeout/request payload
        │   ├── test_security.py          # Password hash/verify 與 JWT 建立/解碼/失效
        │   ├── test_shell_task.py        # Shell task 回傳格式
        │   ├── test_utils_logger.py      # Execution log 寫入/讀取/路徑保護
        │   └── test_worker_schemas.py    # Worker TaskPayload/HeartbeatState schema validation
        ├── integration/             # 跨 API / DB / scheduler / worker 流程測試
        │   ├── test_api.py                  # Auth、job ownership、manual trigger、history、logs API
        │   ├── test_scheduler_flow.py       # Scheduler 掃描 job、dependency、dispatch、rollback
        │   └── test_worker_executor_flow.py # Worker 執行任務、回寫結果、log reference、防重與壞 payload
        └── helpers/
            └── manual_redis_dispatch.py # 手動送 Redis 測試任務的開發輔助腳本
```

## 🚀 本地開啟後端與模擬前端

### 1. 開啟完整後端執行環境

請先確認 Docker Desktop 已啟動，接著在專案根目錄執行：

```bash
docker compose up -d --build
```

這會啟動：

- `backend`：FastAPI API server，對外 port `8000`
- `db`：MySQL
- `redis`：Redis queue
- `backend-worker`：任務執行 worker
- `backend-scheduler`：排程掃描與派發服務
- `frontend`：正式前端容器，對外 port `3000`

確認後端是否啟動成功：

```bash
curl.exe http://localhost:8000/api/health
```

正常會看到：

```json
{"status":"ok"}
```

API 文件：

```text
http://localhost:8000/docs
```

常用 Docker 指令：

```bash
# 查看容器狀態
docker compose ps

# 查看後端 log
docker compose logs backend

# 重啟後端
docker compose restart backend

# 關閉所有服務
docker compose down
```

如果本地 MySQL volume 是舊 schema，後端啟動時會自動補 auth 需要的 `users.email` 與 `users.hashed_password` 欄位。

### 2. 開啟開發測試用模擬前端

模擬前端是單檔 HTML，用來快速測試目前後端完整流程，不是正式產品前端。

建議用 local HTTP server 開，不要直接用 `file://` 雙擊打開：

```bash
cd frontend
python -m http.server 5500
```

瀏覽器開：

```text
http://localhost:5500/backend-flow-test.html
```

頁面中的 `API 根路徑` 請填：

```text
http://localhost:8000/api
```

建議測試順序：

1. 按「檢查後端」
2. 註冊使用者
3. 登入取得 JWT
4. 建立任務
5. 列出我的任務
6. 手動觸發任務
7. 查詢 execution history
8. 查詢 execution detail 與 logs

若前端顯示 `Failed to fetch`，請先確認：

- 測試頁是從 `http://localhost:5500/backend-flow-test.html` 開啟
- API 根路徑是 `http://localhost:8000/api`
- `http://localhost:8000/api/health` 可以正常回 `{"status":"ok"}`
- 修改後端程式後已執行 `docker compose restart backend` 或 `docker compose up -d --build backend`
