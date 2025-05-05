# Use an official Python runtime as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (required for OpenCV and TensorFlow)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    gcc \
    python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Download model (if not pre-downloaded)
# Uncomment if you want Docker to download it:
# RUN apt-get install -y wget && \
#     wget -O /app/static/models/best_model.h5 "https://drive.google.com/uc?id=10gLaaT19nNTxgJp7RrzRZLP01CkNusEG"

# Set environment variables (e.g., for production DB)
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Expose port 5000 (Flask default)
EXPOSE 5000

# Run Flask with Gunicorn (for production)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]