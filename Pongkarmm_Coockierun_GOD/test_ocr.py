import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import cv2
import numpy as np
import pytesseract
import re
import os

# ===== Auto-detect Tesseract =====
TESSERACT_PATHS = [
    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    r'C:\Tesseract-OCR\tesseract.exe',
]
found_tess = False
for tpath in TESSERACT_PATHS:
    if os.path.exists(tpath):
        pytesseract.pytesseract.tesseract_cmd = tpath
        print(f"✅ พบ Tesseract ที่: {tpath}")
        found_tess = True
        break

if not found_tess:
    print("❌ ไม่พบ Tesseract ในทุก path ที่เช็ค!")
    print("   -> กรุณาติดตั้งจาก: https://github.com/UB-Mannheim/tesseract/wiki")
    sys.exit(1)

# ===== โหลดภาพจบเกม =====
img_path = "end_game_result.png"
if not os.path.exists(img_path):
    print(f"❌ ไม่พบไฟล์ {img_path}")
    sys.exit(1)

img = cv2.imread(img_path)
h, w = img.shape[:2]
print(f"\nขนาดภาพ: {w}x{h}")

# ===== ทดสอบ crop หลายพิกัดที่น่าจะเป็นตัวเลขเงิน =====
test_crops = {
    "default (1150,475,1407,541)": (1150, 475, 1407, 541),
    "wider (1050,450,1450,560)":   (1050, 450, 1450, 560),
    "top_bar (600,20,900,70)":     (600, 20, 900, 70),
    "result_area (400,100,1200,700)": (400, 100, 1200, 700),
}

def ocr_crop(img, x1, y1, x2, y2, label=""):
    xmin, xmax = min(x1,x2), max(x1,x2)
    ymin, ymax = min(y1,y2), max(y1,y2)
    cropped = img[ymin:ymax, xmin:xmax]
    if cropped.size == 0:
        print(f"  [{label}] Crop ว่าง!")
        return

    # บันทึก crop ดิบ
    fname = label.replace(" ","_").replace("(","").replace(")","").replace(",","_")
    cv2.imwrite(f"test_crop_{fname}.png", cropped)

    # Upscale 3x + Otsu
    big = cv2.resize(cropped, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(big, cv2.COLOR_BGR2GRAY)
    _, thresh_bin = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    thresh_inv = cv2.bitwise_not(thresh_bin)
    cv2.imwrite(f"test_thresh_{fname}.png", thresh_inv)

    config = r'--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789,'
    results = {}
    for mode_name, mode_img in [("thresh_inv", thresh_inv), ("thresh_bin", thresh_bin), ("gray", gray)]:
        try:
            text = pytesseract.image_to_string(mode_img, config=config).strip()
            nums = re.sub(r'[^\d]', '', text)
            results[mode_name] = (text, nums)
        except Exception as e:
            results[mode_name] = (f"ERROR: {e}", "")

    print(f"\n  [{label}]")
    for mode, (text, nums) in results.items():
        flag = "✅" if nums else "❌"
        print(f"    {flag} {mode}: raw={repr(text)} -> nums={repr(nums)}")

    # ลอง psm 6 ด้วย (block of text)
    config6 = r'--psm 6 --oem 3'
    try:
        text6 = pytesseract.image_to_string(thresh_inv, config=config6).strip()
        print(f"    📝 psm6 (free): {repr(text6)}")
    except Exception as e:
        print(f"    ❌ psm6 error: {e}")

print("\n========== ทดสอบ OCR crop ต่างๆ ==========")
for label, (x1,y1,x2,y2) in test_crops.items():
    ocr_crop(img, x1, y1, x2, y2, label)

print("\n========== เสร็จสิ้น ==========")
print("ดูไฟล์ test_crop_*.png เพื่อตรวจสอบว่า crop ถูกที่ไหม")
