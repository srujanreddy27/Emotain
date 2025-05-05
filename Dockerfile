# Base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (for OpenCV etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV TF_CPP_MIN_LOG_LEVEL=3  # Moved comment to its own line

# Expose port
EXPOSE 5000

# Run Gunicorn with increased timeout
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "120", "app:app"]
