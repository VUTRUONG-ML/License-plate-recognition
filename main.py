from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
from ultralytics import YOLO
from sort.sort import Sort
from util import get_car, read_license_plate


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")  # Kích hoạt SocketIO

# Đặt giới hạn tải lên tối đa cho video (ví dụ: 100MB)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 100MB

# Load các mô hình
coco_model = YOLO('src/Model/yolov8n.pt')  # Mô hình phát hiện xe
license_plate_detector = YOLO('src/Model/license_plate_detector.pt')  # Mô hình phát hiện biển số
mot_tracker = Sort()  # Bộ theo dõi xe

@app.route('/detect_license_plate', methods=['POST'])
def detect_license_plate():
    """
    API nhận diện biển số xe từ video đầu vào và gửi kết quả realtime qua WebSocket.
    """
    video_file = request.files.get('video')
    if not video_file:
        return jsonify({'error': 'Vui lòng cung cấp file video'}), 400

    # Lưu video tạm thời
    video_path = 'Data/input_video.mp4'
    video_file.save(video_path)

    # Mở video
    cap = cv2.VideoCapture(video_path)
    frame_num = -1
    image_height, image_width = 0, 0
    plate_history = {}
    sent_ids = set()

    while True:
        frame_num += 1
        ret, frame = cap.read()
        if not ret or frame is None:
            break

        image_height, image_width = frame.shape[:2]
        line_color = (0, 255, 0)  # Màu xanh lá cây cho vạch vàng
        cv2.line(frame, (0, image_height - 100), (image_width, image_height - 100), line_color, 4)

        # --- Phát hiện xe ---
        detections = coco_model(frame)[0]
        detections_ = []
        for detection in detections.boxes.data.tolist():
            x1, y1, x2, y2, score, classId = detection
            if classId in [2, 3, 5, 7]:  # car, moto, bus, truck
                detections_.append([x1, y1, x2, y2, score])
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 2)  # Màu xanh dương

        # --- Theo dõi xe ---
        if len(detections_) > 0:
            track_ids = mot_tracker.update(np.asarray(detections_))
        else:
            track_ids = np.empty((0, 5))

        # --- Phát hiện biển số ---
        license_plates = license_plate_detector(frame)[0]
        for license_plate in license_plates.boxes.data.tolist():
            x1, y1, x2, y2, score, classId = license_plate
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 255), 2)  # Màu vàng

            # Gán biển số vào xe
            xcar1, ycar1, xcar2, ycar2, carId = get_car(license_plate, track_ids)
            if carId != -1:
                carId = int(carId)
                if carId not in plate_history:
                    plate_history[carId] = []

                # Crop biển số
                license_plate_crop = frame[int(y1):int(y2), int(x1):int(x2), :]

                # OCR biển số
                try:
                    license_plate_text, license_plate_text_score = read_license_plate(license_plate_crop)
                except Exception as e:
                    print(f"Lỗi OCR biển số xe ID {carId} tại frame {frame_num}: {e}")
                    license_plate_text, license_plate_text_score = None, 0.0

                if license_plate_text is not None:
                    plate_history[carId].append({
                        'text': license_plate_text,
                        'text_score': license_plate_text_score,
                        'frame_num': frame_num,
                        'bbox': [x1, y1, x2, y2]
                    })

                # Kiểm tra nếu xe chạm vạch vàng
                if (y1 < 0 or y2 > image_height - 100) and carId not in sent_ids:
                    line_color = (0, 0, 255)  # Đổi màu vạch vàng thành đỏ
                    if plate_history.get(carId) and len(plate_history[carId]) > 0:
                        best = max(plate_history[carId], key=lambda x: x['text_score'])
                        socketio.emit('license_plate_detected', {
                            'car_id': carId,
                            'license_plate': best['text'],
                            'score': best['text_score'],
                            'frame': best['frame_num'],
                            'bbox': best['bbox']
                        })
                        sent_ids.add(carId)

        # Encode frame thành JPEG để gửi qua WebSocket
        _, buffer = cv2.imencode('.jpg', frame)
        frame_data = buffer.tobytes()
        socketio.emit('video_frame', {'frame': frame_data})

    cap.release()

    # Gửi thông báo xử lý xong qua WebSocket
    socketio.emit('processing_complete', {'message': 'Video đã được xử lý xong.'})

    return jsonify({'message': 'Video đã được xử lý xong.'})

@socketio.on('connect')
def handle_connect():
    print("Client đã kết nối!")
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)