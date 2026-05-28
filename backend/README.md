
## 🗄️ 資料庫環境建置與測試 (Database Setup)

請依照以下步驟，在本地端建立並測試 MySQL 資料庫環境：

### 1. 環境變數設定 (.env.local)
請複製根目錄的 `.env.example`，並在 `backend/` 目錄下建立一個新檔案，命名為 `.env.local`。
打開 `.env.local`，將**本地開發區塊**的註解移除。你可以直接使用預設密碼，或視需求改成自己的密碼。

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
# 1. 安裝後端所需套件
pip install -r ./backend/src/requirements.txt

# 2. 執行資料庫模型測試
python ./backend/src/database/test_model.py
```

(💡 提示：如果看到終端機印出「✅ 成功新增 User！」或成功撈出 User 資訊，表示成功)
