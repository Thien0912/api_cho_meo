## Giới thiệu
API Python cung cấp các endpoint để nhận diện giống chó/mèo.
## Mô tả
API ChoMeo là backend cho ứng dụng web hoặc mobile, hỗ trợ:
- Nhận diện giống chó/mèo từ hình ảnh qua các endpoint API.
- Trả về thông tin giống chó/mèo.
- Quản lý tài khoản người dùng (đăng ký, đăng nhập, cập nhật hồ sơ).
## Yêu cầu
- Python >= 3.8
- pip
- MySQL hoặc database tương thích
## Cài đặt
Chạy lệnh:
- git clone https://github.com/Thien0912/api_cho_meo.git
- cd api_cho_meo
- python -m venv venv
- source venv/bin/activate  # Windows: venv\Scripts\activate
- pip install -r requirements.txt
- cp .env.example .env
- Cập nhật thông tin database
- python app.py
- API sẽ chạy tại http://localhost:55010
- Chi tiết API: Xem tài liệu tại /docs
## Công nghệ
- Ngôn ngữ: Python
- Framework: FastAPI
