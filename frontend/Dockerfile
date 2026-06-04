FROM node:22-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

RUN chown -R node:node /app

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
