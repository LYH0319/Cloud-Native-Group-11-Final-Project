# 團隊協作與開發指南 (Contributing Guidelines)

## 0. 開發標準流程 (Daily Workflow)
為了確保大家寫程式時不會互相打架，請所有人每天開發時，嚴格遵守以下四部曲：

1. **出發前先同步**：每天開始寫扣前，先切回 `main` 拉取最新進度，再切回自己的功能分支。
2. **專心在自己的分支寫**：絕對不在 `main` 寫扣。
3. **推扣前先本地格式化與測試**：
   - 前端：執行 `npm run format` 確保排版通過 CI 門檻。
   - 根目錄：執行 `act push` 確保本機模擬全綠。
4. **開 PR**：推上 GitHub 後開 Pull Request

## 1. Git 協作與分支規範
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

### 💡 (附錄) 常用 Git 指令 (Git Cheatsheet)
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