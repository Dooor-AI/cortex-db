FROM node:20-alpine

WORKDIR /app

COPY package*.json ./

# Use cache mount for npm to speed up rebuilds
RUN --mount=type=cache,target=/root/.npm \
    npm install --frozen-lockfile || npm install

COPY . .

RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start"]
