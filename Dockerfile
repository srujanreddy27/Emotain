# Stage 1: Build stage (optional for Python, but useful for compiling dependencies)
FROM python:3.9-slim as builder

WORKDIR /app

# Install system dependencies (required for OpenCV, TensorFlow, etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    gcc \
    python3-dev \
    libgl1 \
    libglib2.0-0 \
    libhdf5-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Download model file (if not included in repo)
RUN mkdir -p static/models && \
    wget -O static/models/best_model.h5 "https://drive.google.com/uc?id=10gLaaT19nNTxgJp7RrzRZLP01CkNusEG"

# Stage 2: Runtime stage
FROM python:3.9-slim

WORKDIR /app

# Copy only necessary files from builder stage
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app/static/models/best_model.h5 /app/static/models/best_model.h5

# Copy application files
COPY . .

# Install runtime system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libhdf5-103 && \
    rm -rf /var/lib/apt/lists/*

# Ensure Python can find user-installed packages
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

# Environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV TF_CPP_MIN_LOG_LEVEL=3  # Suppress TensorFlow debug logs

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s \
  CMD curl -f http://localhost:5000/healthz || exit 1

# Run with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "120", "--workers", "2", "app:app"]
