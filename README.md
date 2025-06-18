## 🚗 Tóm tắt quy trình nhận diện biển số xe từ video (YOLOv8 + PaddleOCR)

Dự án triển khai pipeline nhận diện biển số xe theo thời gian thực từ video đầu vào. Dưới đây là các bước chính:

### 🔹 Bước 1: Nhận video đầu vào
- Người dùng tải video hoặc truyền trực tiếp từ camera (giả lập).
- Backend xử lý và trích xuất từng khung hình (frame) từ video.

### 🔹 Bước 2: Phát hiện xe bằng YOLOv8
- Mỗi khung hình được đưa qua mô hình YOLOv8n để phát hiện các phương tiện giao thông.
- Kết quả là các bounding box xác định vị trí của xe.

### 🔹 Bước 3: Theo dõi xe giữa các khung hình (tracking) bằng Sort
- Gán ID duy nhất cho từng xe và theo dõi vị trí giữa các frame.
- Đảm bảo mỗi xe chỉ nhận diện một lần, tránh trùng lặp.

### 🔹 Bước 4: Xác định vùng chứa biển số xe
- Với mỗi xe, một mô hình YOLO phụ (license_plate_detector) xác định vị trí biển số.
- Vùng biển số được crop từ ảnh gốc để xử lý tiếp.

### 🔹 Bước 5: Nhận diện ký tự trên biển số bằng PaddleOCR
- Biển số được truyền qua PaddleOCR để trích xuất chuỗi ký tự (VD: "51F12345").

### 🔹 Bước 6: Trả kết quả theo thời gian thực qua Socket.IO
- Kết quả gồm: ID xe, số biển số, ảnh có annotate bounding box.
- Dữ liệu được gửi về frontend qua Socket.IO để hiển thị realtime.

---

### 📚 Các công nghệ sử dụng:
- Python, OpenCV
- YOLOv8 (phát hiện xe)
- Sort (theo dõi đối tượng)
- PaddleOCR (nhận diện ký tự)
- Flask (backend API)
- Socket.IO (realtime communication)

