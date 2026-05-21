# 團隊協作與開發指南 (Contributing Guidelines)

## 2. Git 協作與分支規範
1. **禁止直接 Push 到 `main` 分支**。所有新功能與修復請從 `main` 拉出新分支，如果把新功能PR到`main`，在群組通知其他人pull下新版的`main`
2. 一個branch一次一個人做 (不要同時在同一個branch裡面工作)
3. **分支命名原則**：
   - 功能開發：`feat/功能名稱` (例如: `feat/login-api`)
   - 錯誤修復：`fix/錯誤描述` (例如: `fix/cors-error`)
   - 其他：`chore/調整項目` 或 `ci/調整項目`
4. 開發完成後，提交 Pull Request (PR)，並確保 **GitHub Actions 的 CI 檢查完全通過（亮綠燈）** 後才 Merge。

### ✍️ Commit Message 規範
Commit Message 盡量這樣寫會比較清楚：
- **feat**: 新增功能
- **fix**: 修復 Bug
- **ci**: 調整 GitHub Actions, Docker Compose 等 CI/CD 配置
- **chore**: 其他不影響原始碼的雜務（例如修改 .gitignore、更新套件）
- **docs**: 僅修改文件（如 README, CONTRIBUTING）

*範例：`feat(auth): implement JWT login verification`*

### 🎨 程式碼風格 (Code Style)
在本地提交前，請確保執行格式化，否則 CI 將會攔截並拒絕合併：
- **前端 (Frontend)**：請在 `frontend/` 目錄下執行 `npm run format` 來自動排版。
- **後端 (Backend)**：請確保符合 PEP 8 規範，提交前可手動執行 `flake8` 檢查。

### 💡 常用 Git 指令 (Git Cheatsheet)
#### 1. 開始開發新功能（開分支）
```bash
# 確保自己人在 main 分支，並同步線上最新進度
git checkout main
git pull origin main

# 開啟並切換到新功能分支
git checkout -b feat/my-new-feature
```

#### 2. 日常提交程式碼（存檔、本機測試與上傳）
```Bash
# 1. 檢查目前修改了哪些檔案
git status

# 2. 將所有修改過的檔案加入暫存區
git add .

# 3. 提交 Commit (請遵循規範)
git commit -m "feat(frontend): create user dashboard component"

# 4. (選用) 在本地端用 act 轟炸，確保 CI 沒壞
act push

# 5. 推送分支到 GitHub
git push origin feat/my-new-feature
```

#### 3. 同步main進自己的分支（解conflict）
```bash
# 先去把 main 的最新進度拉下來
git checkout main
git pull origin main

# 切回你正在開發的分支
git checkout feat/my-new-feature

# 把 main 的新進度合併進你的分支
git merge main
# (如果有衝突，在 VS Code 裡點選保留哪一版，修改完後存檔，再次 git add . 並且 git commit 即可)
```

#### 4. 把change搬到其他branch
(e.g. if 不小心忘記開分支就直接寫在main裡面了，需要搬到自己的新的branch去)

```bash
# 1. 把目前寫到一半的程式碼全部收進抽屜
git stash

# 2. 切換回 main 確保它是乾淨的，然後開好你的新功能分支
git checkout main
git checkout -b feat/my-correct-feature

# 3. 把抽屜裡的東西拿出來新分支
git stash pop

# 4. 接下來就可以正常的 git add . 和 commit 囉！
git status
```


## 1. 專案開發目錄架構 Project Directory Structure

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
│   ├── README.md                # 前端說明文件 (如何執行 npm install、如何啟動本地開發伺服器（Local Dev Server）、前端的環境變數設定等。)
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
    ├── README.md                # 後端說明文件 (如何建立 Python 虛擬環境、執行 pip install -r requirements.txt、資料庫連線的 .env 怎麼填、如何跑 pytest、以及 FastAPI 的 API 文件路徑等後端專屬資訊。)
    └── requirements.txt         # Python 套件依賴清單

```

