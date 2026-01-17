FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements dan install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy seluruh source code app ke dalam container
COPY app/ ./app/

# Expose port (sesuai config uvicorn nanti)
EXPOSE 8080

# Environment variables default (akan ditimpa oleh Kubernetes Secret)
ENV PORT=8080

# Jalankan aplikasi
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]