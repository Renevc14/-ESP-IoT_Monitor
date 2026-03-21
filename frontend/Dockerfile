# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

ARG VITE_GATEWAY_URL=http://localhost:8000
ARG VITE_ANALYTICS_URL=http://localhost:8004
ARG VITE_WS_URL=ws://localhost:8003

ENV VITE_GATEWAY_URL=$VITE_GATEWAY_URL
ENV VITE_ANALYTICS_URL=$VITE_ANALYTICS_URL
ENV VITE_WS_URL=$VITE_WS_URL

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Stage 2: Serve
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
