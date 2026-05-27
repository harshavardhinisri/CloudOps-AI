FROM node:18-alpine AS builder

WORKDIR /app
COPY package.json ./
RUN npm install

COPY public ./public
COPY src ./src
COPY vite.config.js index.html tailwind.config.js postcss.config.js ./

ARG REACT_APP_API_URL=http://localhost:3001
ENV REACT_APP_API_URL=${REACT_APP_API_URL}

RUN npm run build

FROM node:18-alpine
WORKDIR /app
RUN npm install -g serve
COPY --from=builder /app/dist ./dist

EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})"

CMD ["serve", "-s", "dist", "-l", "3000"]
