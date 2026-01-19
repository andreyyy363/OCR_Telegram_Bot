# Use a lightweight Python base
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install required system packages and Tesseract OCR
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        tesseract-ocr-ukr \
        tesseract-ocr-deu \
        tesseract-ocr-fra \
        tesseract-ocr-ita \
        tesseract-ocr-spa \
        tesseract-ocr-tur \
        tesseract-ocr-chi-sim \
        tesseract-ocr-jpn \
        tesseract-ocr-kor \
        tesseract-ocr-por && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (excluding files via .dockerignore)
COPY bot.py consts.py localization.py reader.py translations.json ./
COPY handlers/ ./handlers/
COPY utils/ ./utils/

# Create necessary directories
RUN mkdir -p static logs

# Set environment variable for Tesseract path
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata

# Run Telegram bot
CMD ["python", "bot.py"]