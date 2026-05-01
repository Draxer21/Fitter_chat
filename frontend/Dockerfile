# Stage 1: Build React (Vite)
FROM node:18-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --ignore-scripts

COPY . .

# Vite uses VITE_* env vars at build time — pass them via --build-arg
ARG VITE_API_BASE_URL=
ARG VITE_GOOGLE_CLIENT_ID=
ARG VITE_CHAT_CONTEXT_KEY=
ARG VITE_MP_PUBLIC_KEY=
ARG VITE_FACEBOOK_CLIENT_ID=

ENV VITE_API_BASE_URL=$VITE_API_BASE_URL \
    VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID \
    VITE_CHAT_CONTEXT_KEY=$VITE_CHAT_CONTEXT_KEY \
    VITE_MP_PUBLIC_KEY=$VITE_MP_PUBLIC_KEY \
    VITE_FACEBOOK_CLIENT_ID=$VITE_FACEBOOK_CLIENT_ID

RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:1.26-alpine

RUN rm /etc/nginx/conf.d/default.conf

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD wget -qO /dev/null http://localhost/nginx-health || exit 1

CMD ["nginx", "-g", "daemon off;"]
