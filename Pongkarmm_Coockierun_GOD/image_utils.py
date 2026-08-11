import cv2
import numpy as np
import subprocess
import random
import time
from adb_utils import get_device_id

def capture_screen(adb_path):
    try:
        device_id = get_device_id(adb_path)

        if not device_id:
            print("❌ [capture_screen] ไม่พบอุปกรณ์ LDPlayer ที่เชื่อมต่อ")
            return None

        cmd = f'"{adb_path}" -s {device_id} exec-out screencap -p'
        result = subprocess.run(cmd, capture_output=True, shell=True)

        if result.returncode != 0 or not result.stdout:
            print("❌ [capture_screen] ส่งคำสั่ง screencap แต่ไม่ได้ข้อมูลภาพกลับมา")
            return None

        img_array = np.frombuffer(result.stdout, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if img is None:
            print("❌ [capture_screen] ไม่สามารถแปลงข้อมูลภาพ (imdecode) ได้")
            return None

        return img

    except Exception as e:
        print(f"❌ [capture_screen] เกิดข้อผิดพลาด: {e}")
        return None

def crop_screen_area(image, bbox):
    """
    ตัดรูปภาพตามพื้นที่ (x1, y1, x2, y2)
    """
    x1, y1, x2, y2 = bbox
    left, right = min(x1, x2), max(x1, x2)
    top, bottom = min(y1, y2), max(y1, y2)
    return image[top:bottom, left:right]

def get_random_pos(x1, y1, x2, y2):
    """ฟังก์ชันช่วยสุ่มพิกัด X, Y ให้อยู่ภายในขอบเขตกรอบสี่เหลี่ยม"""
    rx = random.randint(min(x1, x2), max(x1, x2))
    ry = random.randint(min(y1, y2), max(y1, y2))
    return rx, ry
