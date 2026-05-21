# Cloud-Native-Group-11-Final-Project

## 👥 小組分工 (Team & Responsibilities)
| 姓名 / GitHub | 學號 | 主要負責模組 / 職責 |
| :--- | :--- | :--- |
| **謝羽媞** (@yosoramagician) | 112062315 | 前端 UI 介面設計、使用者註冊 / 登入、Job 註冊與管理 |
| **李沅籈** (@stellae2718) | 112062207 | CI/CD、排程規則設定、任務相依性管理 |
| **謝絜淩** (@Chiehling0214) | 112062220 | 執行結果回報、執行歷史查詢、手動觸發 |
| **廖宇嬅** (@LYH0319) | 112062301 | 任務派發、任務執行、長時間任務處理  |
| **蔡佳倩** (@chien1201) | 112062308 | 任務派發、任務執行、長時間任務處理  |

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
