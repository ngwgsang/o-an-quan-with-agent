# Ô Ăn Quan With Agent

## Giới thiệu

Ứng dụng web kết hợp agent AI để mô phỏng và phân tích trò chơi dân gian Ô Ăn Quan. Dự án gồm backend FastAPI quản lý logic trò chơi, giao diện Jinja2/Tailwind và công cụ CLI phục vụ thử nghiệm mô hình.

## Yêu cầu hệ thống

- Python >= 3.10
- Node.js >= 18 và `npm`
- (Tùy chọn) Môi trường ảo cho Python

## Cài đặt

1. Cài đặt thư viện Python:

   ```bash
   pip install fastapi "uvicorn[standard]" jinja2 togetherai google-genai
   ```

2. Cài đặt các package frontend:

   ```bash
   npm install
   ```
   
## Chạy ứng dụng

### 1. Chạy backend FastAPI
 
-CMD 1 (Venv)
 ```bash
 uvicorn main:app --reload
 ```
 
-CMD 2
Ứng dụng mặc định lắng nghe tại `http://127.0.0.1:8000`.

### 2. Biên dịch CSS bằng Tailwind

 ```bash
 npx tailwindcss -i ./static/css/input.css -o ./static/css/styles.css --watch
```

Giữ tiến trình này chạy song song để CSS tự động cập nhật.

## Cấu trúc thư mục

```
o-an-quan-with-agent/
├── cli/                 # Tiện ích dòng lệnh để chạy thử agent
├── core/                # Logic trò chơi, định nghĩa agent và môi trường
├── eda/                 # Notebook/phân tích dữ liệu hỗ trợ nghiên cứu
├── models/              # Định nghĩa schema dữ liệu và mô hình nội bộ
├── static/              # Tài nguyên tĩnh (CSS, JS, hình ảnh)
├── templates/           # Giao diện Jinja2 cho ứng dụng web
├── logs/                # Nhật ký ván đấu được lưu dưới dạng JSON
├── main.py              # Điểm vào FastAPI
├── package.json         # Cấu hình npm/Tailwind
└── README.md            # Tài liệu dự án (tệp hiện tại)
```
