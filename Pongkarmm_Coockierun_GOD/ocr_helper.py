import cv2
import re

# ===== โหลด EasyOCR =====
try:
    import easyocr
    _OCR_READER = easyocr.Reader(['en'], gpu=False, verbose=False)
    print("✅ [OCR] โหลด EasyOCR สำเร็จ")
except ImportError:
    _OCR_READER = None
    print("⚠️ [OCR] ไม่พบ EasyOCR -> ติดตั้งด้วย: pip install easyocr")

def extract_gold_amount(screen_img, crop_coords=(1150, 475, 1407, 541)):
    """
    ตัดภาพตามพิกัดแล้วอ่านค่าเงินด้วย EasyOCR
    คืนค่า: (gold_int, gold_str)
    """
    if screen_img is None:
        return 0, "0"

    x1, y1, x2, y2 = crop_coords
    xmin, xmax = min(x1, x2), max(x1, x2)
    ymin, ymax = min(y1, y2), max(y1, y2)

    cropped = screen_img[ymin:ymax, xmin:xmax]
    if cropped.size == 0:
        return 0, "ไม่สามารถ Crop ภาพได้"

    # บันทึก crop ไว้ debug
    cv2.imwrite("debug_gold_crop.png", cropped)

    if _OCR_READER is None:
        print("⚠️ [OCR] EasyOCR ไม่พร้อมใช้งาน -> ติดตั้งด้วย: pip install easyocr")
        return 0, "0"

    try:
        results = _OCR_READER.readtext(
            cropped,
            allowlist='0123456789,',
            detail=0,
            paragraph=False
        )
        raw_text = ' '.join(results).strip()
        print(f"🔍 [OCR] ผลการอ่านดิบ: {repr(raw_text)}")
    except Exception as e:
        print(f"⚠️ [OCR Error] EasyOCR อ่านภาพไม่สำเร็จ: {e}")
        return 0, "0"

    clean_number = re.sub(r'[^\d]', '', raw_text)

    if clean_number:
        val = int(clean_number)
        print(f"✅ [OCR] อ่านค่าเงินได้: {val:,} เหรียญ")
        return val, f"{val:,}"
    else:
        print(f"⚠️ [OCR] อ่านตัวเลขไม่ได้ -> ตรวจสอบ debug_gold_crop.png")
        return 0, "0"
