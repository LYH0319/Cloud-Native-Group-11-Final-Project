# Cloud-Native-Group-11-Final-Project

## 👥 小組分工 (Team & Responsibilities)
| 姓名 / GitHub | 學號 | 主要負責模組 / 職責 |
| :--- | :--- | :--- |
| **謝羽媞** (@yosoramagician) | 112062315 | 前端 UI 介面設計、使用者註冊 / 登入、Job 管理 |
| **李沅籈** (@stellae2718) | 112062207 | CI/CD、排程規則設定、資料庫設定 |
| **謝絜淩** (@Chiehling0214) | 112062220 | 執行結果回報、執行歷史查詢、手動觸發 |
| **廖宇嬅** (@LYH0319) | 112062301 | 任務執行、長時間任務處理  |
| **蔡佳倩** (@chien1201) | 112062308 | 任務派發、任務相依性管理、Job 註冊  |

## 🛠️ CI/CD 本地測試指南 (Local CI/CD Testing)

目前ci包含兩個ci測試
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
  - push with changes in frontend/
  - pull request
- including:
  - flake8
  - pytest

### cd
 (我還沒測試過可能會有問題，現在只是隨便弄一個，因為我也不知道要deploy到哪裡)
- on:
  - push to release/ branch

### local ci test
1. 確保電腦已安裝並啟動 **Docker Desktop**
2. 安裝 `act` 工具 (見課程投影片)
3. 執行本地測試命令 (Commands)
    ```
    # 模擬 Git Push 事件，完整跑一遍前後端的所有 CI 流程 (不需要commit)
    act push

	# 如果只想單獨測試前端或後端的 Workflow，可以指定檔案：
	act -W .github/workflows/ci-frontend.yaml
	act -W .github/workflows/ci-backend.yaml
    ```
4. local ci test 如果fail在`Test report`是正常的喔！可以直接push了

## 🛠️ database CRUD 使用指南

目前已完成 User, Job, Execution 的 CRUD 功能。
若需使用，請直接從 `src.database.crud` 引入對應函式。

### 使用建議
- 請務必將 `db: Session` 作為第一個參數傳入。
- 對於涉及狀態變更的操作，請優先使用商業邏輯導向的函數（如 `change_job_status`），而非直接呼叫 `update_job`。
- 若需新增測試，請參考 `tests/database/test_crud.py` 的 AAA 結構。

### 新增功能
如果要請求新增 CRUD 功能，請複製並填寫以下內容告訴我：

	```
    功能名稱：(例如：查詢某個時間區間內的執行紀錄)
    目標資料表：(例如：Execution)
    參數需求：(需要輸入什麼資料？回傳什麼結果？)
    商業邏輯：(是否有特殊的篩選條件或狀態轉換？)
    優先級：(High / Medium / Low)
	```

## 📂 專案開發目錄架構 Project Directory Structure

用前後端分離的架構，所有的程式碼集中在同一個 Repo 裡，請根據你要開發的功能，進入對應的資料夾作業。

以下是我們專案的完整目錄結構：

```text
Cloud-Native-Group-11-Final-Project/
│
├── .github/                 # 放 CI/CD 的 yaml 檔
│   └── workflows/
│       ├── ci-frontend.yaml
│       ├── ci-backend.yaml
│       └── cd.yaml
│
├── docker-compose.yml       # CD 部署用的總指揮
├── .gitignore               # Git 忽略檔案清單 (排除了 .env、__pycache__ 與本地 log 等)
├── README.md                # 專案的總體介紹、系統前後端架構圖、小組成員分工，以及如何一鍵啟動所有服務（例如說明如何使用 docker-compose up）。
├── CONTRIBUTING.md          # 
│
├── frontend/                # Typescript/Javascript
│   ├── package.json
│   ├── src/
│   └── ...
│
└── backend/                 # Python/...?
    │
    ├── config/                  # 系統設定檔
    │   ├── __init__.py
    │   └── settings.py          # 資料庫、排程、權限等環境變數與全域設定
    │
    ├── src/                     # 核心原始碼 (Source Code)
    │   ├── __init__.py
    │   │
    │   ├── api/                 # 使用者層 / 控制層：API 服務 (FastAPI)
    │   │   ├── __init__.py
    │   │   ├── routers/         # API 路由模組
    │   │   │   ├── auth.py      # 使用者註冊/登入管理
    │   │   │   ├── jobs.py      # Job 註冊、修改、刪除與手動觸發 
    │   │   │   └── history.py   # Job 執行歷史紀錄查詢與篩選 
    │   │   └── dependencies.py  # API 權限驗證與角色宣告 (Developer / Operator)
    │   │
    │   ├── scheduler/           # 控制層：排程服務 (Scheduler Service)
    │   │   ├── __init__.py
    │   │   └── cron_scheduler.py# 第一期：單一排程進程，定時掃描 DB 並派發到期任務
    │   │
    |   ├── worker/              # 執行層：任務執行單元 (Data Plane)
    │   │   ├── __init__.py
    │   │   ├── schemas.py    # 任務執行相關的 Pydantic 模型定義
    │   │   ├── executor.py      # 第二期：任務執行與長時間任務
    │   │   └── tasks/           # 實際執行的任務類型定義
    │   │       ├── __init__.py
    │   │       ├── http_task.py # 呼叫外部 REST API 任務
    │   │       └── shell_task.py# 執行 Linux Shell Script 任務
    │   │
    │   ├── database/            # 資料底層 (Metadata Database)
    │   │   ├── __init__.py
    │   │   ├── connection.py    # 資料庫連線實例與 Session 管理 
    │   │   └── models.py        # 資料庫 Schema 模型 (Users, Jobs, Executions 等)
    │   │
    │   └── utils/               # 工具庫 (Utility Functions)
    │       ├── __init__.py
    │       ├── cycle_detection.py # DAG 有向無環圖環狀偵測演算法
    │       └── logger.py        # 負責將 Worker 執行日誌寫入本地硬碟 (EBS Storage)
    │
    ├── tests/                   # 自動化測試單元 (Unit & Integration Tests)
    │   ├── __init__.py
    │   ├── test_api.py          # API 路由功能測試
    │   ├── test_dispatch.py         # 目前是在還沒完成任務派發前的任務執行的模擬測試(因為沒有任務所以DB還沒法更新)
    │   └── test_scheduler.py    # 排程與相依性檢查邏輯測試
    │
    ├── .env                     # 本地環境變數設定檔（內含資料庫密碼等，不進入 Git 追蹤）
    └── requirements.txt         # Python 套件依賴清單

```
