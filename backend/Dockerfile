# 使用 Python 3.10 輕量版環境
FROM python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 複製環境清單並安裝
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 將後端程式碼全部複製進去
COPY . .

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
