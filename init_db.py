from database import MongoDB

def initialize_database():
    mongo_db = MongoDB()
    if mongo_db.check_connection():
        mongo_db.initialize_biensoxedangky()
        mongo_db.initialize_history()
        print("Khởi tạo dữ liệu thành công.")

if __name__ == "__main__":
    initialize_database()
