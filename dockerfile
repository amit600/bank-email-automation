# ============================================
# Bank Email Automation System — Dockerfile
# ============================================
FROM python:3.11-slim

# Metadata
LABEL maintainer="Bank Email Automation"
LABEL description="AI-powered email processing with Llama 3 + Agentic AI"

# Environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        tesseract-ocr \
        libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Working directory
WORKDIR /app

# Install Python dependencies (cached layer)
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . .

# Create logs directory
RUN mkdir -p logs/attachments

# Expose ports
# 8000 — Mock Banking API
# 8501 — Streamlit UI
EXPOSE 8000 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default: run Mock Banking API
# Override with: docker run ... python main.py
# Or: docker run ... streamlit run ui/approval_app.py
CMD ["uvicorn", "apis.main:app", "--host", "0.0.0.0", "--port", "8000"]