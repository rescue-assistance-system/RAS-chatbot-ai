# --- Stage 1: Build dependencies ---
FROM python:3.10-slim-bookworm as builder

WORKDIR /install

# Cài đặt gói hệ thống cần thiết để build
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install-deps -r requirements.txt

# --- Stage 2: Final image ---
FROM python:3.10-slim-bookworm

WORKDIR /app

# Chỉ copy lại những gì đã cài (không mang theo build tools)
COPY --from=builder /install-deps /usr/local

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
