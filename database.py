from pymongo import MongoClient

class MongoDB:
    def __init__(self, uri="mongodb://localhost:27017", db_name="license_plate_db"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]

    def get_collection(self, collection_name):
        return self.db[collection_name]

    def check_connection(self):
        """
        Kiểm tra kết nối với MongoDB.
        """
        try:
            self.client.admin.command('ping')  # Gửi lệnh 'ping' đến MongoDB
            print("Kết nối MongoDB thành công!")
            return True
        except Exception as e:
            print(f"Lỗi kết nối MongoDB: {e}")
            return False
    def initialize_biensoxedangky(self):
        """
        Khởi tạo collection biensoxedangky với các trường mặc định.
        """
        collection = self.db["biensoxedangky"]
        if collection.count_documents({}) == 0:  # Nếu collection rỗng
            collection.insert_many([
                {"bienso": "51H18844", "tien": 300000},
                {"bienso": "60A71944", "tien": 300000},
                {"bienso": "55H88155", "tien": 500000},
                {"bienso": "51D58995", "tien": 300000}
            ])
        return collection    
    def initialize_history(self):
        """
        Khởi tạo collection history với các trường mặc định.
        """
        collection = self.db["history"]
        if collection.count_documents({}) == 0:  # Nếu collection rỗng
            collection.insert_many([
                {"bienso": "30A-12345", "tien": 500000, "trangthai": "Đã thanh toán"},
                {"bienso": "29B-67890", "tien": 300000, "trangthai": "Thanh toán thất bại"},
                {"bienso": "51C-54321", "tien": 700000, "trangthai": "Không đủ tiền"}
            ])
        return collection
# Khởi tạo kết nối MongoDB
mongo_db = MongoDB()