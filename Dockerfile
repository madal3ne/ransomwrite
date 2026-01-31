# Use official Python runtime
FROM python:3.11-slim

# Set workdir
WORKDIR /app

# Install system deps for PIL/OpenCV and Tesseract (required for OCR)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy app
COPY . /app

# Expose port (default shown, overridden by runtime $PORT)
EXPOSE 5000

# Run with gunicorn. Use environment variables so PaaS providers (e.g. Render)
# can inject the correct $PORT and optionally configure the number of workers
# via $GUNICORN_WORKERS.
CMD ["sh", "-lc", "gunicorn -w ${GUNICORN_WORKERS:-4} -b 0.0.0.0:${PORT:-5000} app:app"]
