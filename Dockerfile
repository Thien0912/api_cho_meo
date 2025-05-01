# Sử dụng image chính thức của Ubuntu 22.04
FROM ubuntu:22.04 AS builder

# Tránh các thông báo tương tác khi cài đặt
ENV DEBIAN_FRONTEND=noninteractive

# Cập nhật, bật kho universe và cài đặt các gói hệ thống cần thiết
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    libatlas-base-dev \
    libblas-dev \
    liblapack-dev \
    libpng-dev \
    libfreetype6-dev \
    libxml2-dev \
    libxslt-dev \
    libjpeg-dev \
    zlib1g-dev \
    git \
    curl \
    unzip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

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
