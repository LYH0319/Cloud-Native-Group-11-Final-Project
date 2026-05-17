# Cloud-Native-Group-11-Final-Project

## 📂 專案核心目錄結構 (Project Directory Structure)


```text
Cloud-Native-Group-11-Final-Project/
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
│   │   ├── executor.py      # 第一期：In-Process Thread 任務執行與超時控制
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
│   └── test_scheduler.py    # 排程與相依性檢查邏輯測試
│
├── .env                     # 本地環境變數設定檔（內含資料庫密碼等，不進入 Git 追蹤）
├── .gitignore               # Git 忽略檔案清單 (排除了 .env、__pycache__ 與本地 log 等)
├── README.md                # 專案說明文件
└── requirements.txt         # Python 套件依賴清單
```