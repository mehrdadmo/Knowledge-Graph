FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for OCR (Tesseract, etc.)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-fas \
    libtesseract-dev \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies with increased timeout
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 300 --retries 3 -r requirements.txt

# Copy application
COPY app/ ./app/

# Run as non-root user
RUN useradd -m -u 1000 ocruser && chown -R ocruser:ocruser /app
USER ocruser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8765"]