# Stage 1: Build frontend
FROM node:24-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Production image
FROM python:3.13-slim
WORKDIR /app

# Install Python dependencies
COPY backend/requirements.lock .
RUN pip install --no-cache-dir --require-hashes -r requirements.lock

# Copy backend code
COPY backend/ .

# Copy built frontend from stage 1
COPY --from=frontend-builder /frontend/dist ./static

# Create data directory and user
# Use UID/GID 1000 to match typical host user
RUN mkdir -p /app/data && \
    addgroup --gid 1000 appuser && \
    adduser --disabled-password --gecos "" --uid 1000 --gid 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD ["python", "-c", "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4).status == 200 else 1)"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
