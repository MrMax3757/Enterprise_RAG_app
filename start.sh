#!/bin/bash
set -e

# Port configuration (supports Hugging Face Spaces port 7860, Render/Koyeb $PORT, or default 8501)
STREAMLIT_PORT=${PORT:-7860}
BACKEND_PORT=8000

echo "🚀 Starting Enterprise Agentic RAG services..."

# Start FastAPI backend in background
uvicorn app.main:app --host 127.0.0.1 --port $BACKEND_PORT &

# Wait for FastAPI backend to be ready
echo "⏳ Waiting for FastAPI backend to become healthy on port $BACKEND_PORT..."
until curl -s http://127.0.0.1:$BACKEND_PORT/ > /dev/null; do
    sleep 1
done
echo "✅ FastAPI backend is live!"

# Start Streamlit frontend in foreground
echo "🌐 Starting Streamlit frontend on port $STREAMLIT_PORT..."
exec streamlit run ui/app.py \
    --server.port=$STREAMLIT_PORT \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false

