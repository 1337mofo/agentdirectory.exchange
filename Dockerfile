# Agent Directory Exchange - Railway Deployment
FROM python:3.11-slim

WORKDIR /app

# Copy all necessary files
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY Agent_Directory_Whitepaper.pdf ./

# Install Python dependencies (Updated 2026-02-13 12:42 GMT+7)
WORKDIR /app/backend
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (Railway sets PORT env var)
ENV PORT=8000
EXPOSE $PORT

# Start uvicorn (JSON array format for proper execution)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
