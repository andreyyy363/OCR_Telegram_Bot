# Use a lightweight Python base
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Create static directory in the correct location (working directory)
RUN mkdir -p static

# Install required packages and Tesseract
RUN apt-get update && \
        apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-ukr tesseract-ocr-deu tesseract-ocr-fra  \
    tesseract-ocr-ita tesseract-ocr-spa tesseract-ocr-tur tesseract-ocr-chi-sim tesseract-ocr-jpn tesseract-ocr-kor  \
    tesseract-ocr-por && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -r requirements.txt

# Define build argument
ARG TOKEN
# Set it as an environment variable
ENV TOKEN=$TOKEN

# Run Telegram bot
CMD ["python", "bot.py"]