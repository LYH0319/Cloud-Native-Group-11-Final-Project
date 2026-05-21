# 使用 Node.js 輕量版環境 (配合你們 CI 設定的 Node 版本)
FROM node:22-alpine

# 設定工作目錄
WORKDIR /app

# 將 package.json 複製進去
COPY package.json ./

# 安裝套件
RUN npm install

# 將其餘程式碼複製進去
COPY . .

# ⚠️ 救火指令：因為還沒寫啟動伺服器的 code，先用 sleep 讓容器保持存活
CMD ["sh", "-c", "sleep infinity"]

# 未來等前端寫好後，再把上面那行改成類似這樣：
# CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]