FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 1. Install Library Python Dulu
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Copy Script Download tadi
COPY download_model.py .

# 3. [PENTING] Jalankan script download SAAT BUILD
RUN python download_model.py

# 4. Copy sisa kode aplikasi
COPY app/ ./app/

# Expose port
EXPOSE 80

ENV MODEL_NAME="/app/model_cache"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]