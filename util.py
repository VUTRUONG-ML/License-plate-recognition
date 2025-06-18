import string
import re
import cv2
from paddleocr import PaddleOCR
from skimage.filters import threshold_local
# Khởi tạo PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='en')  # Sử dụng mô hình tiếng Anh

# mapping dictionary for character conversion (chỉ ánh xạ các ký tự dễ nhầm lẫn)
dict_char_to_int = {
    'O': '0',  # Chữ 'O' ánh xạ thành số 0
    'A': '4',  # Chữ 'A' ánh xạ thành số 4
    'I': '1',  # Chữ 'I' ánh xạ thành số 1
    'J': '3',  # Chữ 'J' ánh xạ thành số 3
    'G': '6',  # Chữ 'G' ánh xạ thành số 6
    'S': '5',  # Chữ 'S' ánh xạ thành số 5
    'B': '8'
}

# Reverse mapping dictionary
dict_int_to_char = {v: k for k, v in dict_char_to_int.items()}

def format_license_plate(text):
    """
    Chuyển đổi chuỗi biển số xe thành định dạng chuẩn của biển số xe Việt Nam.
    Định dạng:
    - 7 ký tự: XXA-YYYYY (VD: 30A-12345)
    - 8 ký tự: XXA-YYY.YY (VD: 30G-123.45)
    Args:
        text (str): Chuỗi ký tự biển số xe nhận diện được từ OCR.
    Returns:
        str: Chuỗi biển số xe đã được chuẩn hóa.
    """
    # Chuẩn hóa chuỗi ký tự
    for char in text:
        if(char not in string.ascii_letters and char not in string.digits):
            text = text.replace(char, '')

    formatted_text = ''
    i = 0
    # [0:2]: Chuyển ký tự dễ nhầm lẫn thành số
    while i < len(text):
        if 0 <= i <= 1 or 3 <= i < len(text):
            if text[i] in dict_char_to_int.keys():
                formatted_text  += dict_char_to_int[text[i]]
            else:   
                formatted_text += text[i]
        elif i == 2:
            if text[i] in dict_int_to_char.keys():
                formatted_text += dict_int_to_char[text[i]]
            else:
                formatted_text += text[i]
        i += 1
    
    return formatted_text


def license_complies_format(text):
    """
    Kiểm tra xem chuỗi text có đúng định dạng biển số xe Việt Nam hay không.
    Args:
        text (str): Chuỗi ký tự biển số xe.
    Returns:
        bool: True nếu đúng định dạng, False nếu không.
    """
    # Định dạng biển số xe Việt Nam:
    # - 7 ký tự: XXA-YYYYY (VD: 30A-12345)
    # - 8 ký tự: XXA-YYY.YY (VD: 30G-123.45)
    pattern = r'^\d{2}[A-Z]\d{5}$'  # Định dạng Biển số xe VN 
    # Kiểm tra chuỗi với từng định dạng
    if re.match(pattern, text):
        return True
    return False

# Trả về vị trí chiếc xe mà biển số này thuộc về 
def get_car(license_plate, vehicle_track_ids):
    """Là bước gán biển số cho đúng xe (track_id) bằng cách so sánh tọa độ bounding box.
    biết biển số này thuộc về chiếc xe nào đang được theo dõi
    
    cách thức: tìm cái bbox của biển số nằm trong bbox của xe nào thì gán cho xe đó
    """
    x1, y1, x2, y2, score, classId = license_plate
    for vehicle in vehicle_track_ids:
        x1_vehicle, y1_vehicle, x2_vehicle, y2_vehicle, carId = vehicle
        if x1 > x1_vehicle and y1 > y1_vehicle and x2 < x2_vehicle and y2 < y2_vehicle:
            # Nếu bbox của biển số nằm trong bbox của xe thì gán cho xe đó
            return x1_vehicle, y1_vehicle, x2_vehicle, y2_vehicle, carId
    # Nếu không tìm thấy xe nào thì trả về 0
    return -1, -1, -1, -1, -1

# Đọc kí tự trong biển số xe 
def read_license_plate(license_plate_crop):
    """
    Trả về ký tự trong biển số và độ tin cậy score, sử dụng PaddleOCR.
    Args:
        license_plate_crop (numpy.ndarray): Ảnh biển số đã cắt.
    Returns:
        tuple: Chuỗi ký tự biển số đã chuẩn hóa và độ tin cậy (score).
    """
    # Lưu ảnh biển số tạm thời để PaddleOCR xử lý
    temp_image_path = "temp_license_plate.jpg"
    cv2.imwrite(temp_image_path, license_plate_crop)

    # Nhận diện văn bản từ ảnh bằng PaddleOCR
    results = ocr.ocr(temp_image_path, cls=True)

    if results is None or len(results) == 0 or results[0] is None or len(results[0]) == 0:
        return None, None

    # Lấy ký tự từ kết quả OCR
    text = ""
    for i, line in enumerate(results[0]):  # Duyệt qua từng dòng kết quả
        text += line[1][0]  # Lấy văn bản từ kết quả OCR (chỉ lấy phần văn bản)

        # Kiểm tra nếu đoạn văn bản có 3 ký tự và có dòng tiếp theo dài 5 ký tự
        if len(text) == 3 and i + 1 < len(results[0]):
            next_line = results[0][i + 1][1][0]  # Lấy dòng tiếp theo
            if len(next_line) == 5:  # Nếu phần tiếp theo có 5 ký tự
                text += next_line  # Ghép chúng lại với nhau thành 1 biển số hoàn chỉnh
                
        score = line[1][1]  # Lấy độ tin cậy từ kết quả OCR
        text = text.replace(' ', '').upper()  # Chuyển đổi thành chữ hoa và loại bỏ khoảng trắng
        formatted_text = format_license_plate(text)  # Chuẩn hóa chuỗi ký tự
        # print(f"Formatted Text: {formatted_text}")  # Debug: In chuỗi đã chuẩn hóa
        if license_complies_format(formatted_text):  # Kiểm tra định dạng biển số
            # print(f"Detected Text: {text}, Score: {score}")  # Debug: In chuỗi nhận diện được
            return formatted_text, score  # Trả về chuỗi đã chuẩn hóa và độ tin cậy
        text = ""

    return None, None  # Nếu không nhận diện được, trả về None

def write_csv(results, output_path):
    """
    write the results to a csv file
    args:
        results: dictionary containing the results
        output_path: path to save the csv file
    """
    with open(output_path, 'w') as f:
        f.write('{},{},{},{},{},{},{}\n'.format('frame_num', 'car_id', 'car_bbox', 
                                                'license_plate_bbox', 'license_plate_bbox_score', 'license_number', 
                                                'license_number_score'))
        for frame_num in results.keys():
            for car_id in results[frame_num].keys():
                if 'car' in results[frame_num][car_id].keys() and \
                    'license_plate' in results[frame_num][car_id].keys() and \
                    'text' in results[frame_num][car_id]['license_plate'].keys():
                    f.write('{},{},{},{},{},{},{}\n'.format(frame_num, 
                                                            car_id,
                                                            '[{}, {}, {}, {}]'.format(
                                                                results[frame_num][car_id]['car']['bbox'][0],
                                                                results[frame_num][car_id]['car']['bbox'][1],
                                                                results[frame_num][car_id]['car']['bbox'][2],
                                                                results[frame_num][car_id]['car']['bbox'][3]),
                                                                '[{}, {}, {}, {}]'.format(
                                                                    results[frame_num][car_id]['license_plate']['bbox'][0],
                                                                    results[frame_num][car_id]['license_plate']['bbox'][1],
                                                                    results[frame_num][car_id]['license_plate']['bbox'][2],
                                                                    results[frame_num][car_id]['license_plate']['bbox'][3]),
                                                                results[frame_num][car_id]['license_plate']['bbox_score'],
                                                                results[frame_num][car_id]['license_plate']['text'],
                                                                results[frame_num][car_id]['license_plate']['text_score'])
                        )
        f.close()

def get_best_license_plate(results):
    """
    Lấy biển số có score cao nhất cho mỗi xe.
    Args:
        results (dict): Kết quả nhận diện từ các frame.
    Returns:
        dict: Biển số tốt nhất cho mỗi xe.
    """
    best_plates = {}

    for frame_num, cars in results.items():
        for car_id, data in cars.items():
            if 'license_plate' in data and 'text' in data['license_plate']:
                license_plate = data['license_plate']
                text = license_plate['text'] 
                score = license_plate['text_score']

            if car_id not in best_plates or score > best_plates[car_id]['text_score']:
                best_plates[car_id] = {
                    'text': text,
                    'text_score': score,
                    'bbox': license_plate['bbox'],
                    'frame_num': frame_num
                }

    return best_plates

def preprocess_license_plate(license_plate_crop):
    """
    Xử lý ảnh biển số để chuẩn bị tách ký tự.
    Args:
        license_plate_crop (numpy.ndarray): Ảnh biển số đã cắt.
    Returns:
        numpy.ndarray: Ảnh nhị phân sau khi xử lý.
    """
    # Chuyển ảnh sang ảnh xám
    gray = cv2.cvtColor(license_plate_crop, cv2.COLOR_BGR2GRAY)

    # Áp dụng adaptive threshold
    T = threshold_local(gray, 15, offset=10, method="gaussian")
    binary = (gray > T).astype("uint8") * 255

    # Đảo ngược màu (nền trắng, ký tự đen)
    binary = cv2.bitwise_not(binary)

    return binary