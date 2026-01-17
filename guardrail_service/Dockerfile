FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements dan install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY app/ ./app/

# Environment Variables
ENV PORT=80
ENV MODEL_NAME="treamyracle/indobert-ner-pii-guardrail"

# Expose port (default http)
EXPOSE 80

# Jalankan server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]