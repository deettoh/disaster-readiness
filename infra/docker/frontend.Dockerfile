# Frontend Dockerfile for React Application with Vite and Nginx

FROM node:20-alpine AS builder
# Build stage
# Install dependencies and build React app with Vite into static files.

WORKDIR /app/apps/frontend

COPY apps/frontend/package.json apps/frontend/package-lock.json ./
RUN npm ci

COPY apps/frontend ./

ARG VITE_API_BASE_URL=http://localhost:8000/api/v1
ARG VITE_MAPTILER_KEY=
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_MAPTILER_KEY=$VITE_MAPTILER_KEY

RUN npm run build

# Runtime stage
# Serve static files with Nginx.
FROM nginx:1.27-alpine

COPY infra/docker/frontend.nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/apps/frontend/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
