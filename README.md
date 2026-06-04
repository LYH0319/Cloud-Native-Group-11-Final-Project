# Cloud-Native Group 11 Final Project

本專案是一個雲原生任務排程與執行系統，採前後端分離架構。前端使用 React + TypeScript + Vite，後端使用 FastAPI，並透過 MySQL、Redis、Scheduler 與 Worker 完成 Job 建立、排程、派發、執行、紀錄與查詢。

## 快速啟動整個專案

建議使用 Docker Compose 一次啟動完整前後端與基礎服務。

### 1. 前置需求

- Docker Desktop
- Git
- 若要本機開發前端，需要 Node.js 與 npm
- 若要本機開發後端，需要 Python 3.10 以上

### 2. 準備後端環境變數

在專案根目錄確認 `backend/.env` 存在。若尚未建立，可由範例檔複製：

```bash
copy backend\.env.example backend\.env
```

Docker Compose 會使用 `backend/.env` 啟動 MySQL 與後端服務。Docker 環境中的 `DATABASE_URL` 應指向 Compose service name `db`，例如：

```text
DATABASE_URL=mysql+pymysql://api_worker:PASSWORD_group11@db:3306/job_scheduler
```

若要啟用「忘記密碼」的 email reset link，請在 `backend/.env` 設定 SMTP。以 Gmail 為例：

```text
RESET_PASSWORD_BASE_URL=http://localhost:3000
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_FROM=noreplyjobschedulersystem@gmail.com
SMTP_FROM_NAME=Job Scheduler System
SMTP_USERNAME=noreplyjobschedulersystem@gmail.com
SMTP_PASSWORD=your-gmail-app-password
```

注意：

- `SMTP_USERNAME` 必須是完整 Gmail 地址。
- `SMTP_PASSWORD` 必須是 Google 產生的 16 字元 App Password，不是一般 Gmail 登入密碼。
- `SMTP_FROM_NAME` 只是寄件者顯示名稱，不可拿來當 SMTP username。
- 若未設定 `SMTP_HOST`，後端會把 reset link 印在 backend log，方便本機開發測試。
- Docker Compose 使用 `backend/.env`，修改後請重啟 backend：

```bash
docker compose restart backend
```

### 3. 啟動完整服務

在專案根目錄執行：

```bash
docker compose up -d --build
```

這會啟動：

| Service | 說明 | 對外網址 |
| :--- | :--- | :--- |
| `frontend` | React/Vite 前端 | `http://localhost:3000` |
| `backend` | FastAPI 後端 API | `http://localhost:8000` |
| `db` | MySQL 8.4 | 僅 Compose 內部網路 |
| `redis` | Redis queue | 僅 Compose 內部網路 |
| `backend-worker` | 任務執行 Worker | 僅 Compose 內部網路 |
| `backend-scheduler` | 排程掃描與派發服務 | 僅 Compose 內部網路 |

開啟前端：

```text
http://localhost:3000
```

檢查後端健康狀態：

```bash
curl.exe http://localhost:8000/api/health
```

正常會回傳：

```json
{"status":"ok"}
```

FastAPI 文件：

```text
http://localhost:8000/docs
```

### 4. 常用 Docker 指令

```bash
# 查看服務狀態
docker compose ps

# 查看全部 log
docker compose logs

# 查看後端 log
docker compose logs backend

# 查看 worker log
docker compose logs backend-worker

# 重新 build 並啟動
docker compose up -d --build

# 重啟後端
docker compose restart backend

# 停止所有服務
docker compose down
```

若要同時啟動多個 worker：

```bash
docker compose up -d --build --scale backend-worker=3
```

## 本機開發啟動方式

Docker Compose 是完整專案最推薦的啟動方式。若需要分開開發前端或後端，可參考以下流程。

### 後端本機開發

進入後端目錄：

```bash
cd backend
```

安裝套件：

```bash
python -m pip install -r requirements.txt
```

啟動 API：

```bash
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

注意：

- 後端需要可連線的 MySQL 與 Redis。
- 若後端在本機直接執行，`DATABASE_URL` 不能使用 Docker 內部 hostname `db`，需改成可從本機連到的 MySQL 位址，例如 `localhost`。
- 目前 `docker-compose.yml` 沒有把 MySQL 與 Redis port publish 到 host，所以完整本機後端開發時，需要另外開本機 MySQL/Redis，或調整 Compose port 設定。

### 前端本機開發

進入前端目錄：

```bash
cd frontend
```

安裝套件：

```bash
npm install
```

啟動 Vite：

```bash
npm run dev
```

開啟：

```text
http://localhost:5173
```

注意：前端 API 使用 `/api`，並透過 `frontend/vite.config.ts` proxy 到後端。Docker 內執行時 target 是 `http://backend:8000`。如果你在本機直接跑 `npm run dev`，需要把 proxy target 改成：

```text
http://localhost:8000
```

或使用 Docker Compose 的 `frontend` service，直接開 `http://localhost:3000`。

## 專案開發目錄架構

```text
Cloud-Native-Group-11-Final-Project/
|
|-- .github/
|   `-- workflows/
|       |-- ci-backend.yaml          # 後端 CI：flake8、pytest
|       |-- ci-frontend.yaml         # 前端 CI：typecheck、format check、test
|       `-- cd.yaml                  # CD workflow 範例
|
|-- backend/                         # FastAPI 後端、Scheduler、Worker
|   |-- config/
|   |   `-- setting.py               # 後端設定與環境變數
|   |
|   |-- src/
|   |   |-- api/
|   |   |   |-- main.py              # FastAPI app、CORS、router 掛載、health check
|   |   |   |-- dependencies.py      # API dependency，例如 current user
|   |   |   |-- security.py          # API 安全相關輔助
|   |   |   |-- schemas.py           # API schema 輔助
|   |   |   `-- routers/
|   |   |       |-- auth.py          # 註冊、登入、使用者認證
|   |   |       |-- jobs.py          # Job 建立、查詢、狀態更新、手動觸發
|   |   |       `-- history.py       # Execution history、rerun、logs 查詢
|   |   |
|   |   |-- database/
|   |   |   |-- core.py              # SQLAlchemy engine/session、DB 初始化
|   |   |   |-- connection.py        # database 對外相容匯出
|   |   |   |-- models.py            # User、Job、Execution、Dependency、LogReference
|   |   |   |-- schemas.py           # Pydantic schemas
|   |   |   `-- crud.py              # CRUD 與任務業務邏輯 helper
|   |   |
|   |   |-- scheduler/
|   |   |   `-- cron_scheduler.py    # 掃描到期 Job，建立 execution 並派發任務
|   |   |
|   |   |-- worker/
|   |   |   |-- executor.py          # Worker 主流程、任務 dispatch 與回報
|   |   |   |-- queue_manager.py     # Redis queue 操作
|   |   |   |-- schemas.py           # Worker payload schema
|   |   |   `-- tasks/
|   |   |       |-- http_task.py       # HTTP 任務執行
|   |   |       `-- shell_task.py    # Shell 任務執行
|   |   |
|   |   `-- utils/
|   |       |-- cycle_detection.py   # Job dependency cycle detection
|   |       |-- email.py             # Password reset email / SMTP helper
|   |       |-- logger.py            # Execution log 寫入與讀取
|   |       `-- security.py          # 密碼 hash、JWT 建立與驗證
|   |
|   |-- tests/
|   |   |-- unit/                   # 單元測試
|   |   |-- integration/            # API、DB、Scheduler、Worker 整合測試
|   |   `-- helpers/                # 手動測試輔助腳本
|   |
|   |-- Dockerfile                  # FastAPI backend image
|   |-- Dockerfile.worker           # Worker / Scheduler image
|   |-- requirements.txt            # Python dependencies
|   |-- pytest.ini                  # pytest 設定
|   |-- .env.example                # 後端環境變數範例
|   `-- .env                        # 後端實際環境變數，本機不提交敏感資訊
|
|-- frontend/                       # React + TypeScript + Vite 前端
|   |-- public/                     # 靜態資源
|   |-- src/
|   |   |-- App.tsx                 # 前端路由與主 app
|   |   |-- api.ts                  # API 呼叫 helper
|   |   |-- main.tsx                # React entry
|   |   |-- index.css               # 全域樣式
|   |   |-- components/             # 共用元件與 route guard
|   |   |-- pages/                  # Login、Admin、Operator、Developer、JobMonitor 等頁面
|   |   |-- types/                  # TypeScript 型別
|   |   `-- assets/                 # 圖片與前端資源
|   |
|   |-- tests/                      # 前端測試
|   |-- backend-flow-test.html      # 開發用單檔 API flow 測試頁
|   |-- Dockerfile                  # Frontend image
|   |-- package.json                # npm scripts 與 dependencies
|   |-- vite.config.ts              # Vite 設定與 API proxy
|   |-- vitest.config.ts            # Vitest 設定
|   `-- tsconfig*.json              # TypeScript 設定
|
|-- logs/                           # Worker execution logs 掛載目錄
|-- docker-compose.yml              # 一次啟動 frontend/backend/db/redis/worker/scheduler
|-- CONTRIBUTING.md                 # 協作規範
`-- README.md                       # 專案說明
```

## 測試與檢查

### 後端測試

```bash
cd backend

# 全部後端測試
python -m pytest

# 只跑 unit tests
python -m pytest -m unit

# 只跑 integration tests
python -m pytest -m integration

# CI 使用的語法級 flake8 檢查
python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
```

### 前端測試

```bash
cd frontend

# TypeScript type check
npm run typecheck

# Vitest
npm test

# Prettier check
npm run format:check

# Production build
npm run build
```

## 開發用 API Flow 測試頁

`frontend/backend-flow-test.html` 是開發用的單檔測試頁，可快速測：

- health check
- 註冊與登入
- 忘記密碼與 email reset link
- 建立 Job
- 列出 Job
- 手動觸發 Job
- 查詢 execution history
- 查詢 execution detail 與 logs

啟動方式：

```bash
cd frontend
python -m http.server 5500
```

瀏覽器開啟：

```text
http://localhost:5500/backend-flow-test.html
```

頁面中的 API 根路徑請填：

```text
http://localhost:8000/api
```

## CI/CD 本地測試

若要用 `act` 模擬 GitHub Actions：

```bash
# 模擬 push，跑完整 workflow
act push

# 單獨跑前端或後端 workflow
act -W .github/workflows/ci-frontend.yaml
act -W .github/workflows/ci-backend.yaml
```

## 常見問題

### 前端顯示 Failed to fetch

請確認：

- 後端健康檢查 `http://localhost:8000/api/health` 可以回傳 `{"status":"ok"}`
- Docker Compose 前端請開 `http://localhost:3000`
- 本機 Vite 前端請確認 `vite.config.ts` proxy target 指到可連線的後端

### 後端連不到資料庫

請確認：

- `backend/.env` 存在
- Docker Compose 環境的 `DATABASE_URL` host 是 `db`
- 若後端在本機直接跑，`DATABASE_URL` host 需改成 `localhost` 或其他本機可連的 MySQL 位址

### 忘記密碼寄信失敗

若前端顯示：

```text
SMTP email delivery failed. Please check SMTP_USERNAME and SMTP_PASSWORD.
```

請確認：

- `backend/.env` 的 `SMTP_USERNAME` 是完整 Gmail 地址，例如 `noreplyjobschedulersystem@gmail.com`
- `SMTP_PASSWORD` 是 Gmail App Password，不是一般登入密碼
- 該 Gmail 帳號已開啟 2-Step Verification
- 修改 `.env` 後已重啟 backend：`docker compose restart backend`
- 若只是本機測試、不想真的寄信，可暫時註解 `SMTP_HOST`，後端會把 reset link 印在 backend log

Gmail App Password 取得方式：

1. 前往 Google 帳戶安全性頁面：`https://myaccount.google.com/security`
2. 開啟 2-Step Verification
3. 前往 App Passwords：`https://myaccount.google.com/apppasswords`
4. 建立一組 App Password，名稱可填 `Job Scheduler System`
5. 將產生的 16 字元密碼填入 `SMTP_PASSWORD`

### 忘記密碼帳號未綁定 email

若使用者忘記密碼，但帳號沒有 email，前端會顯示：

```text
此帳號未綁定 email，請聯絡管理員重設密碼
```

此時請由 Admin 進入管理者專區，在帳號清單中點選「重設密碼」替使用者設定新密碼。

### 修改後端程式後沒有生效

可重啟後端服務：

```bash
docker compose restart backend
```

若有 dependency 或 Dockerfile 變更，請重新 build：

```bash
docker compose up -d --build backend
```
