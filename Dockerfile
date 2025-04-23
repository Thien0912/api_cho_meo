# Sử dụng image chính thức của Ubuntu 22.04
FROM ubuntu:22.04 AS builder

# Tránh các thông báo tương tác khi cài đặt
ENV DEBIAN_FRONTEND=noninteractive

# Cập nhật, bật kho universe và cài đặt các gói hệ thống cần thiết
RUN apt-get update && apt-get install -y \
    software-properties-common && \
    add-apt-repository universe && \
    apt-get update && apt-get install -y \
    python3 python3-pip git nano htop \
    wget gnupg unzip \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libgdk-pixbuf2.0-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    libu2f-udev \
    libvulkan1 \
    libxss1 \
    libxtst6 \
    libgbm1 \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt Google Chrome Stable
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get update && \
    apt-get install -y ./google-chrome-stable_current_amd64.deb && \
    rm google-chrome-stable_current_amd64.deb

# Thiết lập thư mục làm việc
WORKDIR /_app_

# Sao chép mã nguồn
COPY app /_app_/app
COPY chatbot /_app_/chatbot
COPY ingestion /_app_/ingestion
COPY utils /_app_/utils
COPY .env /_app_/.env
COPY requirements.txt /_app_/requirements.txt
COPY run_api.py /_app_/run_api.py

# Cài đặt thư viện Python
RUN pip3 install --no-cache-dir --upgrade -r /_app_/requirements.txt

# Xóa thư mục ảo nếu có
RUN rm -rf /_app_/.venv || true

# Chạy ứng dụng
CMD ["python3", "run_api.py"]
