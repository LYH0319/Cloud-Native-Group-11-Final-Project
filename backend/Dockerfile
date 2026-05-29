# 使用 Python 3.10 輕量版環境
FROM python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 複製環境清單並安裝
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 將後端程式碼全部複製進去
COPY . .

# ⚠️ 救火指令：一樣先讓容器保持存活，不要掛掉
CMD ["sh", "-c", "sleep infinity"]

# 未來等 FastAPI 寫好後，再把上面那行改成這樣：
# CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]