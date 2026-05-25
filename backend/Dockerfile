FROM python:3.13-slim

WORKDIR /app

# System deps for lxml (pandas read_html) and compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libxml2-dev libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download TextBlob corpora at build time
RUN python -m textblob.download_corpora

# Create logs directory
RUN mkdir -p /app/logs

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "1200"]
