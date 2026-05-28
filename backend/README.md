
## 🗄️ 資料庫環境建置與測試 (Database Setup)

請依照以下步驟，在本地端建立並測試 MySQL 資料庫環境：

### 1. 環境變數設定 (.env.local)
請複製根目錄的 `.env.example`，並在 `backend/` 目錄下建立兩個新檔案，命名為 `.env`跟`.env.local`。
根據裡面的註解設定下半部分的URL
密碼的部分可以直接使用預設密碼，或視需求改成自己的密碼。

### 2. 啟動 MySQL 容器
確保你的電腦已開啟 **Docker Desktop**。
在**專案根目錄**下，開啟終端機 (Console) 並執行以下指令：

```bash
docker compose up -d
```

(💡 提示：如果執行後看到綠色的 Started 或 Running，代表資料庫已經順利在背景啟動！)

### 3. 測試資料庫連線

回到終端機，依序執行：

```
cd backend

# 1. 安裝後端所需套件
pip install -r ./requirements.txt

# 2. 執行資料庫CRUD測試
pytest tests/database/test_crud.py -v      
```

(💡 提示：如果看到終端機印出「✅ 成功新增 User！」或成功撈出 User 資訊，表示成功)

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