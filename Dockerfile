# Use official lightweight Python 3.11 image
FROM python:3.11-slim

# Set system environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    BACKEND_URL=http://127.0.0.1:8000 \
    HOME=/home/user

# Install system dependencies (curl for healthcheck, build tools for native wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user (required for Hugging Face Spaces and container security)
RUN useradd -m -u 1000 user
WORKDIR $HOME/app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY --chown=user:user . .

# Make start script executable
RUN chmod +x start.sh

# Switch to non-root user
USER user

# Hugging Face Spaces uses port 7860 by default; Render/Koyeb inject $PORT
EXPOSE 7860

# Launch both FastAPI backend and Streamlit UI
CMD ["./start.sh"]

