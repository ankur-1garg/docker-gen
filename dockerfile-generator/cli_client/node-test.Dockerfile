FROM harbor.your-company.com/custom-images/node:18-alpine-secure

WORKDIR /app

COPY package*.json ./

RUN npm ci

COPY . .

EXPOSE 3000

CMD ["node", "index.js"]