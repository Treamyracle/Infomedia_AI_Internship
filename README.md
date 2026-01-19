# 🛡️ DompetKu Secure AI Agent (Internship Project)

> **Secure Customer Support AI Agent** dengan integrasi **PII Guardrail** (Regex & NER) untuk melindungi data sensitif pengguna sebelum diproses oleh LLM.

![Status](https://img.shields.io/badge/Status-Development-yellow)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-green)
![Guardrail](https://img.shields.io/badge/PII-Protection-red)

## 📖 Ringkasan Project

Project ini adalah implementasi **AI Agent Customer Support** untuk layanan E-Wallet "DompetKu". Sistem ini dirancang dengan fokus utama pada **Keamanan Data (Data Privacy)**.

Sebelum pesan pengguna dikirim ke otak AI (Gemini 2.0 via Google ADK), pesan tersebut melewati layer **Guardrail Service** terpisah yang mendeteksi dan menyensor (masking) data sensitif seperti NIK, Email, No HP, Nama, dan Alamat.

### ✨ Fitur Utama
1.  **Smart AI Agent:** Menggunakan **Google ADK (Agent Development Kit)** dan **Gemini 2.0 Flash**.
2.  **Multi-Layer Guardrail:**
    * **Regex:** Mendeteksi NIK, Email, No HP, Tanggal Lahir, No Rekening.
    * **NER (Named Entity Recognition):** Model `IndoBERT` custom untuk mendeteksi Nama Orang & Alamat.
3.  **Secure Vault Mechanism:** Data asli disimpan sementara di server (Vault) dan hanya direstorasi saat *Function Calling* dieksekusi, sehingga LLM tidak pernah melihat data asli.
4.  **Microservices Architecture:** Agent dan Guardrail berjalan sebagai service terpisah di Kubernetes.
5.  **Real-time Dashboard:** UI Web untuk memantau chat, latency, penggunaan RAM/CPU, dan data terdeteksi.

---

## 🏗️ Arsitektur Sistem

Sistem ini menggunakan pola **PII Masking Guardrail** dengan komunikasi HTTP antar service.

![Arsitektur DompetKu Secure AI Agent](https://github.com/Treamyracle/Infomedia_AI_Internship/blob/main/content/chart.png)

## 🚀 Cara Menjalankan (Step-by-Step)

### Prasyarat
- Docker Desktop (dengan Kubernetes enabled).
- Google Gemini API Key (Dapatkan di AI Studio).
- Git.

---

### 1. Clone Repository
```bash
git clone https://github.com/Infomedia_AI_Internship.git
cd Infomedia_AI_Internship
```

### 2. Konfigurasi API Key (Kubernetes Secret)
Anda perlu membuat secret untuk menyimpan API Key agar aman. Ganti `MASUKKAN_GOOGLE_API_KEY_ANDA` dan `MASUKKAN_HUGGINGFACE_TOKEN_ANDA_JIKA_PERLU` dengan nilai sebenarnya.

```powershell
# Hapus secret lama jika ada
kubectl delete secret infomedia-secrets --ignore-not-found

# Buat secret baru (Windows)
kubectl create secret generic infomedia-secrets `
  --from-literal=GOOGLE_API_KEY="MASUKKAN_GOOGLE_API_KEY_ANDA" `
  --from-literal=HF_TOKEN="MASUKKAN_HUGGINGFACE_TOKEN_ANDA_JIKA_PERLU"
```

Selanjutnya masukkan environment variable anda

```bash
# Buat secret baru (Linux/macOS/WSL)
kubectl create secret generic infomedia-secrets \
  --from-literal=GOOGLE_API_KEY="MASUKKAN_GOOGLE_API_KEY_ANDA" \
  --from-literal=HF_TOKEN="MASUKKAN_HUGGINGFACE_TOKEN_ANDA_JIKA_PERLU"
```

---

### 3. Build Docker Images
Kita perlu membangun image untuk kedua service.

```powershell
# 1. Build Guardrail Service (NER Model akan di-download saat build ini)
# Proses ini mungkin memakan waktu 2-5 menit tergantung koneksi internet
docker build -t guardrail-service:latest ./guardrail_service

# 2. Build Agent Service
docker build -t agent-service:latest ./agent_service
```

---

### 4. Deploy ke Kubernetes
Jalankan manifest deployment yang ada di folder `k8s/`.

```powershell
# Apply semua konfigurasi
kubectl apply -f k8s/01-guardrail-deployment.yaml
kubectl apply -f k8s/02-guardrail-service.yaml
kubectl apply -f k8s/03-agent-deployment.yaml
kubectl apply -f k8s/04-agent-service.yaml

# Cek status pods (Tunggu hingga STATUS 'Running')
kubectl get pods -w
```

---

### 5. Akses Aplikasi
Setelah semua Pods berjalan (Running), lakukan port-forwarding untuk mengakses Web UI.

```powershell
# Forward port 8080 dari service agent ke localhost
kubectl port-forward service/agent-service 8080:8080
```

Buka browser dan akses: `http://localhost:8080`

---
## 🧠 Penjelasan Teknis Guardrail

Sistem Guardrail bekerja dalam dua lapisan (layers) untuk memastikan keamanan data maksimal.

#### 1. Regex Engine (`regex_engine.py`)
Layer pertama menggunakan *Regular Expressions* untuk mendeteksi pola data terstruktur yang pasti. Engine ini memindai teks dan menggantinya dengan tag placeholder sebelum teks menyentuh model AI.

**Pola yang dideteksi:**
* **NIK:** 16 digit angka (`\b\d{16}\b`).
* **Email:** Format standar email.
* **Nomor Telepon:** Format Indonesia (+62/62/08) diikuti 8-12 digit.
* **Tanggal Lahir:** Format DD-MM-YYYY.
* **Nomor Rekening:** 10-12 digit angka.

> **Logic Khusus:** Engine memiliki logika untuk membedakan *Nomor Rekening* dan *Nomor Telepon*. Jika terdeteksi deretan angka 10-12 digit tetapi diawali dengan "08" atau "62", sistem akan mengabaikannya sebagai nomor rekening untuk menghindari *false positive*.

#### 2. NER Engine (`ner_engine.py`)
Layer kedua menggunakan model *Deep Learning* (BERT) untuk mendeteksi entitas yang tidak memiliki pola angka pasti, seperti Nama Orang dan Alamat.

* **Model:** `treamyracle/indobert-ner-pii-guardrail` (Fine-tuned IndoBERT).
* **Library:** HuggingFace Transformers `pipeline`.
* **Arsitektur:** Menggunakan pola **Singleton Pattern** untuk memastikan model hanya dimuat satu kali ke dalam memori (RAM) saat aplikasi start, sehingga hemat resource dan inferensi lebih cepat.
* **Output:** Mengembalikan list entitas (PERSON, ADDRESS, NIK, EMAIL, PHONE, BIRTHDATE, BANK_NUM) beserta posisi karakter (start/end) untuk dilakukan masking.
---

## 🧪 Skenario Pengujian (Test Cases)
Gunakan kalimat berikut untuk menguji kemampuan AI dan Guardrail di Web UI:

### 📋 Data Mock Database
Berikut adalah data dummy hardcoded yang tersimpan di sistem (`agent_service/app/tools.py`). Gunakan informasi ini untuk memvalidasi respon Agent (misalnya mencocokkan NIK dengan Saldo atau Alamat).

```python
DATABASE_USER = {
    "1234567890123456": {
        "nama": "Arif Athaya",
        "email": "arif@example.com",
        "tgl_lahir": "04-10-2005",
        "phone": "08123456789",
        "alamat": "Jl. Emerald Alona G 43",
        "saldo": 5000000,
        "pin": "123456"
    },
    "3201123456789001": {
        "nama": "Budi Santoso",
        "email": "budi@test.com",
        "tgl_lahir": "17-08-1990",
        "phone": "089988776655",
        "alamat": "Jl. Sudirman No 1 Jakarta",
        "saldo": 150000,
        "pin": "654321"
    }
}
```

#### Ganti Password (Validasi PII Lengkap)  
**Input:**
```perl
"Saya lupa password. Tolong reset untuk NIK 1234567890123456, email arif@example.com, tanggal lahir 04-10-2005."
```
**Ekspektasi:** Data disensor di dashboard, tetapi AI berhasil memproses reset password.

#### Request Kartu Fisik (NER Detection: Nama & Alamat)  
**Input:**
```arduino
"Kirim kartu fisik atas nama Budi Santoso, alamat di Jl. Sudirman No 1 Jakarta, nomor hp 089988776655."
```
**Ekspektasi:** Nama "Budi Santoso" dan Alamat "Jl. Sudirman..." terdeteksi sebagai `[REDACTED_PERSON]` dan `[REDACTED_ADDRESS]`.

#### Withdraw (Logic Check & Security)  
**Input:**
```arduino
"Tarik saldo NIK 1234567890123456 ke rekening 1234567890 milik Joko Widodo."
```
**Ekspektasi:** Gagal. AI menolak karena nama pemilik rekening tidak sesuai dengan nama pemilik akun dompet.

---

## 📊 Resource & Performance Report
Berikut adalah laporan performa dari Guardrail Service (NER Model) saat dijalankan di environment lokal.

### Spesifikasi Environment

| Komponen | Spesifikasi |
|---|---|
| Device | Laptop |
| CPU Model | i7-11800HQ (8 Cores, 16 Threads) |
| RAM Total | 16 GB |
| OS / Environment | Windows 11 (WSL 2) / Docker Desktop |
| Kubernetes Limits | CPU: 6 Core (Limit), RAM: 4Gi (Limit) |

### Benchmark Inference (Guardrail Service)  
Pengukuran dilakukan menggunakan `psutil` internal pada endpoint `/clean` (Regex + NER IndoBERT).

| Metric | Rata-rata (Average) | Peak (Maksimum) | Keterangan |
|---:|---:|---:|---|
| NER Inference Latency | ~500 ms | 620 ms | Waktu proses per Inference NER |
| CPU Usage | 20% | 50% | Melonjak saat start awal |
| Memory Usage | 1740 MB | 1800 MB | Stabil (Model loaded in memory) |

**Catatan:** Latency ~3000-5000ms dianggap wajar untuk cold inference model BERT pada CPU. Untuk production, disarankan menggunakan GPU atau model yang dikuantisasi (ONNX/Quantized) untuk latency <100ms.

---

## 📂 Struktur Project

```text
/
├── agent_service/           # [Backend] Logika AI Agent & Tools
│   ├── app/
│   │   ├── static/          # Frontend Web UI
│   │   │   └── index.html
│   │   ├── __init__.py
│   │   ├── core_agent.py    # Logika Google ADK & Flow
│   │   ├── main.py          # Entry point FastAPI
│   │   └── tools.py         # Mock Database & Functions
│   ├── Dockerfile
│   └── requirements.txt
│
├── content/                 # Aset gambar untuk dokumentasi/README
│   └── chart.png
│
├── guardrail_service/       # [Backend] Security & ML Service
│   ├── app/
│   │   ├── __pycache__/     # Cache Python (Compiled bytecode)
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI Endpoint (/clean)
│   │   ├── ner_engine.py    # Logic Model IndoBERT
│   │   └── regex_engine.py  # Logic Regex PII
│   ├── model_cache/         # Folder tempat model disimpan setelah download
│   ├── Dockerfile
│   ├── download_model.py    # Script download model saat build
│   └── requirements.txt
│
├── k8s/                     # [Deployment] Kubernetes Manifests
│   ├── 00-secrets.yaml      
│   ├── 01-guardrail-deployment.yaml
│   ├── 02-guardrail-service.yaml
│   ├── 03-agent-deployment.yaml
│   └── 04-agent-service.yaml
│
├── .gitignore
└── README.md
```

