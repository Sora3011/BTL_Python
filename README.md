# 📊 Hệ thống Phân tích Cảm xúc Bình luận - ViSoBERT v2 + SQL

Ứng dụng web phân tích cảm xúc (Sentiment Analysis) bình luận từ **YouTube** và **Facebook** sử dụng mô hình **ViSoBERT v2** (Vietnamese Social BERT) kết hợp cơ sở dữ liệu **SQLite**.

## ✨ Tính năng chính

- **Quét bình luận YouTube** tự động từ link video
- **Phân tích bình luận Facebook** qua file CSV hoặc nhập trực tiếp
- **Phân loại cảm xúc 4 nhãn**: Tích cực / Trung tính / Tiêu cực / Hỗn hợp
- **Temperature Scaling** để calibrate xác suất dự đoán
- **Tiền xử lý thông minh**: chuyển emoticon → tiếng Việt, xử lý emoji, giảm ký tự lặp
- **Lưu trữ dữ liệu** vào SQLite với quan hệ khóa ngoại (Posts ↔ Comments)
- **Dashboard trực quan** với biểu đồ Plotly và truy vấn SQL (JOIN, GROUP BY)

## 🛠️ Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| Giao diện web | Streamlit |
| Mô hình AI | ViSoBERT v2 (XLMRoberta - transformers) |
| Cơ sở dữ liệu | SQLite |
| Biểu đồ | Plotly |
| Cào dữ liệu | youtube-comment-downloader |

## 📦 Cài đặt

### 1. Clone repository
```bash
git clone https://github.com/Sora3011/BTL_Python.git
cd BTL_Python
```

### 2. Tạo môi trường ảo và cài thư viện
```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

### 3. Tải model ViSoBERT v2
Đặt các file model vào thư mục `Model_viso_bert_v2/`:
- `config.json`
- `inference_config.json`
- `model.safetensors`
- `tokenizer.json`
- `tokenizer_config.json`

> ⚠️ File `model.safetensors` (~390MB) không được đưa lên GitHub. Liên hệ nhóm để nhận file model.

### 4. Chạy ứng dụng
```bash
streamlit run app.py
```

## 📁 Cấu trúc dự án

```
BTL_Python/
├── app.py                      # Điểm khởi chạy ứng dụng Streamlit
├── requirements.txt            # Danh sách thư viện Python
├── .gitignore                  # Cấu hình bỏ qua tệp khi commit Git
├── README.md                   # Tài liệu hướng dẫn sử dụng
├── Model_viso_bert_v2/         # Thư mục chứa mô hình ViSoBERT v2
│   ├── config.json
│   ├── inference_config.json
│   ├── model.safetensors       # (không đưa lên GitHub)
│   ├── tokenizer.json
│   └── tokenizer_config.json
├── sentiment_analytics.db      # Cơ sở dữ liệu SQLite
├── frontend/                   # Giao diện người dùng
│   ├── assets/
│   │   └── style.css           # Định kiểu giao diện CSS
│   ├── components/             # Các thành phần giao diện tái sử dụng
│   │   ├── style_loader.py     # Nạp file CSS vào Streamlit
│   │   ├── header.py           # Tiêu đề và thông tin phân hệ
│   │   ├── sidebar.py          # Thanh điều hướng và thông số hệ thống
│   │   ├── cards.py            # Thẻ thống kê và hiển thị kết quả
│   │   └── charts.py           # Biểu đồ trực quan hóa dữ liệu
│   └── views/                  # Các màn hình phân hệ
│       ├── overview_view.py    # Phân hệ Tổng quan & Phân tích dữ liệu
│       ├── youtube_view.py     # Phân hệ Thu thập & Phân tích YouTube
│       └── facebook_view.py    # Phân hệ Phân tích bình luận Facebook
└── backend/                    # Xử lý dữ liệu và mô hình AI
    ├── database/
    │   └── db.py               # Thao tác và kết nối cơ sở dữ liệu SQLite
    ├── models/
    │   └── sentiment_model.py  # Nạp mô hình ViSoBERT v2 và dự đoán cảm xúc
    ├── scrapers/
    │   ├── text_preprocessor.py # Tiền xử lý và làm sạch văn bản
    │   └── youtube_scraper.py  # Thu thập bình luận từ YouTube
    └── services/
        └── analysis_service.py # Điều phối luồng xử lý và lưu trữ dữ liệu
```

## 👥 Nhóm thực hiện

Bài tập lớn môn Python

## 📄 License

MIT License
