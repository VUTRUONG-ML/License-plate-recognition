import requests

with open("E:/PythonSource/NhanDangBienSoXe/Data/4.mp4", "rb") as f:
    files = {'video': f}
    res = requests.post("http://127.0.0.1:5000/detect_license_plate", files=files)

print(res.json())
