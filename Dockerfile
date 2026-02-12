# Agent Directory Exchange - Railway Deployment
FROM python:3.11-slim

WORKDIR /app

# Copy backend code
COPY backend/ ./backend/

# Install Python dependencies
WORKDIR /app/backend
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (Railway sets PORT env var)
ENV PORT=8000
EXPOSE $PORT

# Start uvicorn
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
