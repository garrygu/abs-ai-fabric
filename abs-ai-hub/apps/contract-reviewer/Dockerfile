FROM python:3.11-slim

# sys deps for OCR and PDFs
RUN apt-get update && apt-get install -y \
    tesseract-ocr ocrmypdf poppler-utils gcc g++ git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py /app/
COPY prompts /app/prompts
COPY policy /app/policy

ENV PYTHONUNBUFFERED=1
CMD ["python", "-u", "app.py"]
