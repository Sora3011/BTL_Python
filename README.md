# 📊 Hệ thống Phân tích Cảm xúc Bình luận - ViSoBERT_final + SQL

Ứng dụng web **Sounds of Social** phân tích cảm xúc (Sentiment Analysis) bình luận từ **YouTube** và **Facebook** sử dụng mô hình **ViSoBERT_final** (Vietnamese Social BERT) kết hợp cơ sở dữ liệu **SQLite**.

## ✨ Tính năng chính

- **Quét bình luận YouTube** tự động từ link video (ưu tiên bình luận mới nhất, hỗ trợ Full Mode & Config Mode)
- **Phân tích bình luận Facebook** qua tệp CSV (tự động nhận diện cột bình luận & tác giả) hoặc nhập trực tiếp
- **Phân loại cảm xúc 4 nhãn**: Tích cực / Trung tính / Tiêu cực / Hỗn hợp
- **Hiệu chuẩn suy luận**: hỗ trợ Logit Adjustment (`neutral_bias = 0.0`), Temperature Scaling (`T = 1.3`) và gắn cờ cảnh báo độ tin cậy (`confidence_threshold = 0.70`)
- **Định lượng rủi ro**: tính điểm chuẩn hóa Score 0–100, xét 5 cấp độ rủi ro kết hợp Shannon Entropy trung bình $H(P)$, và lọc bình luận phân vân nổi bật ($H(P) > 0.75$)
- **Tiền xử lý đặc thù tiếng Việt**: khử URL/mention, chuyển emoticon → tiếng Việt, xử lý emoji, rút gọn ký tự lặp
- **Lưu trữ dữ liệu** vào SQLite với quan hệ khóa ngoại (`posts` ↔ `comments`) và tự động nâng cấp lược đồ (`ALTER TABLE`)
- **Dashboard trực quan** với biểu đồ Plotly và truy vấn SQL (`JOIN`, `GROUP BY`)

## 🛠️ Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| Giao diện web | Streamlit |
| Mô hình AI | ViSoBERT_final (XLMRoberta - transformers) |
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

### 3. Tải model ViSoBERT_final
Đặt các file model vào thư mục `Model_viso_bert_v3/`:
- `config.json`
- `inference_config.json`
- `model.safetensors`
- `tokenizer.json`
- `tokenizer_config.json`

> ⚠️ Thư mục `Model_viso_bert_v3/` (gồm `model.safetensors` ~390MB) không được đưa lên GitHub. Liên hệ nhóm để nhận file model.

### 4. Chạy ứng dụng
```bash
streamlit run app.py
```

## 📁 Cấu trúc dự án

```
BTL_Python/
├── app.py                        # Điểm khởi chạy ứng dụng Streamlit
├── requirements.txt              # Danh sách thư viện Python
├── .gitignore                    # Cấu hình bỏ qua tệp khi commit Git
├── README.md                     # Tài liệu hướng dẫn sử dụng
├── model1611.ipynb               # Notebook nghiên cứu dữ liệu, WeightedTrainer & đối chứng
├── btl-python.ipynb              # Notebook huấn luyện và thử nghiệm song song
├── Model_viso_bert_v3/           # Thư mục chứa mô hình ViSoBERT_final đang triển khai
│   ├── config.json
│   ├── inference_config.json
│   ├── model.safetensors         # (không đưa lên GitHub)
│   ├── tokenizer.json
│   └── tokenizer_config.json
├── Model_5cd_visobert/           # Checkpoint 5CD-AI dùng để đối chứng thực nghiệm
├── sentiment_analytics.db        # Cơ sở dữ liệu SQLite
├── frontend/                     # Giao diện người dùng
│   ├── assets/
│   │   └── style.css             # Định kiểu giao diện CSS
│   ├── components/               # Các thành phần giao diện tái sử dụng
│   │   ├── style_loader.py       # Nạp file CSS và HTML vào Streamlit
│   │   ├── navbar.py             # Thanh thương hiệu Sounds of Social
│   │   ├── cards.py              # Thẻ thống kê, cockpit và live terminal
│   │   └── charts.py             # Biểu đồ trực quan hóa dữ liệu Plotly
│   └── views/                    # Các màn hình phân hệ
│       ├── overview_view.py      # Phân hệ Tổng quan & Phân tích dữ liệu
│       ├── youtube_view.py       # Phân hệ Thu thập & Phân tích YouTube
│       └── facebook_view.py      # Phân hệ Phân tích bình luận Facebook
└── backend/                      # Xử lý dữ liệu và mô hình AI
    ├── database/
    │   └── db.py                 # Khởi tạo, nâng cấp lược đồ & thao tác SQLite
    ├── models/
    │   └── sentiment_model.py    # Nạp mô hình ViSoBERT_final và suy luận cảm xúc
    ├── scrapers/
    │   ├── text_preprocessor.py  # Tiền xử lý và làm sạch văn bản
    │   └── youtube_scraper.py    # Thu thập bình luận mới nhất từ YouTube
    └── services/
        └── analysis_service.py   # Điều phối luồng xử lý và lưu trữ dữ liệu
```

## 👥 Nhóm thực hiện

Bài tập lớn môn Python

## 📄 License

MIT License
