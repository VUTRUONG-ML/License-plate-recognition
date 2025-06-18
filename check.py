
if __name__ == '__main__':
    # Khởi tạo bảng biensoxedangky nếu chưa có
    mongo_db.initialize_biensoxedangky()
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)