# Sử dụng Python 3.9 làm base image
FROM python:3.9-slim-buster

# Cài đặt các gói phụ thuộc
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Tạo thư mục app và đặt làm thư mục làm việc
RUN mkdir /app
WORKDIR /app

# Sao chép các file requirements và cài đặt các thành phần của ứng dụng
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn vào container
COPY . .

# Chạy chương trình khi khởi động container
CMD ["python", "main.py"]
