import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import subprocess
import time
import os
import random
import cv2
import numpy as np
import setup_boost
import requests
import re

# ===== โหลด EasyOCR (ไม่ต้องติดตั้ง binary ภายนอก) =====
try:
    import easyocr
    _OCR_READER = easyocr.Reader(['en'], gpu=False, verbose=False)
    print("✅ [OCR] โหลด EasyOCR สำเร็จ")
except ImportError:
    _OCR_READER = None
    print("⚠️ [OCR] ไม่พบ EasyOCR -> ติดตั้งด้วย: pip install easyocr")

# 1. โหลดไฟล์ Config.json
def load_config(config_path="Config.json"):
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            print("✅ โหลดไฟล์ Config.json สำเร็จ")
            return config
    except FileNotFoundError:
        print("❌ ไม่พบไฟล์ Config.json กรุณาตรวจสอบตำแหน่งไฟล์")
        return None

# 2. ฟังก์ชันดึง Device ID จาก ADB
def get_device_id(adb_path):
    try:
        get_dev_cmd = f'"{adb_path}" devices'
        dev_result = subprocess.run(get_dev_cmd, capture_output=True, text=True, shell=True)
        
        for line in dev_result.stdout.strip().split("\n")[1:]:
            if "device" in line and not line.startswith("*"):
                return line.split()[0]
        return None
    except Exception:
        return None

# 3. ฟังก์ชันเปิดเกมผ่าน ADB
def start_game(config):
    adb_path = config.get("adb_path", "adb")
    target_package = config.get("target_package")
    target_activity = config.get("target_activity")

    if target_package and target_activity:
        print(f"🚀 กำลังเปิดเกม: {target_package}...")
        cmd = f'"{adb_path}" shell am start -n {target_package}/{target_activity}'
        subprocess.run(cmd, capture_output=True, text=True, shell=True)
        print("✅ ส่งคำสั่งเปิดเกมเรียบร้อยแล้ว!")
        time.sleep(5)  # รอเกมโหลดแป๊บนึงหลังสั่งเปิด
    else:
        print("❌ ไม่พบข้อมูล target_package หรือ target_activity ใน Config.json")

# 4. ฟังก์ชันส่งคำสั่งคลิก (Tap) ผ่าน ADB
def tap_button(adb_path, device_id, x, y):
    rx = x + random.randint(-3, 3)
    ry = y + random.randint(-3, 3)
    
    cmd = f'"{adb_path}" -s {device_id} shell input tap {rx} {ry}'
    subprocess.run(cmd, shell=True)
    print(f"👆 [Click] กด/Pop-up ที่พิกัด: ({rx}, {ry})")

# 5. แคปหน้าจอโดยใช้ device ที่เชื่อมต่อเรียบร้อยแล้ว
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

# 6. ฟังก์ชันตรวจเช็ค State หน้า Loby
def check_loby_state(screen_img, templates_dir):
    if screen_img is None:
        print("screen_img is None")
        return False

    template_path = f"{templates_dir}/lobby.png"
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    
    if template is None:
        print(f"❌ ไม่พบไฟล์รูป {template_path}")
        return False

    # ===================================================
    # ⚡ STEP 1: Fast Check (เช็คเฉพาะโซน X: 966->715, Y: 1098->640)
    # ===================================================
    x1, y1 = 966, 715
    x2, y2 = 1098, 640
    
    ymin, ymax = min(y1, y2), max(y1, y2)
    xmin, xmax = min(x1, x2), max(x1, x2)

    roi = screen_img[ymin:ymax, xmin:xmax]

    if roi.shape[0] >= template.shape[0] and roi.shape[1] >= template.shape[1]:
        res_fast = cv2.matchTemplate(roi, template, cv2.TM_CCOEFF_NORMED)
        _, max_val_fast, _, _ = cv2.minMaxLoc(res_fast)

        if max_val_fast >= 0.95:
            print(f"✅ [Fast Check] ยืนยันอยู่หน้า Loby! (ความเหมือน: {max_val_fast*100:.1f}%)")
            return True

    # ===================================================
    # 🔍 STEP 2: Fallback Search (ถ้า Fast Check ไม่เจอ ค่อยหาทั้งจอ)
    # ===================================================
    print("⚠️ Fast Check ไม่เจอ -> กำลังค้นหาหน้า Loby แบบกวาดทั้งหน้าจอ...")
    res_full = cv2.matchTemplate(screen_img, template, cv2.TM_CCOEFF_NORMED)
    _, max_val_full, _, _ = cv2.minMaxLoc(res_full)

    if max_val_full >= 0.95:
        print(f"✅ [Full Search] เจอหน้า Loby บนหน้าจอ! (ความเหมือน: {max_val_full*100:.1f}%)")
        return True
    
    print(f"❌ ไม่อยู่หน้า Loby (ความเหมือนสูงสุดแค่: {max_val_full*100:.1f}%)")
    return False

# 7. ⭐ [เพิ่มใหม่] ฟังก์ชันจัดการหน้าแปลก / เคลียร์ Pop-up (วนลูปเช็ครูปในโฟลเดอร์ notfound)
def resolve_unknown_state(screen_img, adb_path, notfound_dir="notfound", threshold=0.6):
    if screen_img is None:
        return False

    if not os.path.exists(notfound_dir):
        print(f"⚠️ ไม่พบโฟลเดอร์ '{notfound_dir}'")
        return False

    valid_extensions = (".png", ".jpg", ".jpeg")
    image_files = [f for f in os.listdir(notfound_dir) if f.lower().endswith(valid_extensions)]

    if not image_files:
        print(f"⚠️ ไม่มีไฟล์รูปในโฟลเดอร์ '{notfound_dir}'")
        return False

    device_id = get_device_id(adb_path)
    if not device_id:
        return False

    print("🔍 [Unknown State] กำลังวนลูปเช็คปุ่มแก้ไขในโฟลเดอร์ notfound...")

    for filename in image_files:
        img_path = os.path.join(notfound_dir, filename)
        template = cv2.imread(img_path, cv2.IMREAD_COLOR)

        if template is None:
            continue

        res = cv2.matchTemplate(screen_img, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)

        if max_val >= threshold:
            h, w, _ = template.shape
            center_x = max_loc[0] + (w // 2)
            center_y = max_loc[1] + (h // 2)

            print(f"🎯 เจอรูปแก้สถานะ: '{filename}' (ความเหมือน: {max_val*100:.1f}%)")
            tap_button(adb_path, device_id, center_x, center_y)
            return True

    print("❌ ไม่พบรูปปุ่มแก้ไขใดๆ ในโฟลเดอร์ notfound ที่ตรงกับหน้าจอปัจจุบัน")
    return False


# ===== ฟังก์ชัน OCR อ่านค่าเงิน =====
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
        # EasyOCR รับ numpy array BGR โดยตรง ไม่ต้อง preprocess ก็ได้
        # allowlist เฉพาะตัวเลขและคอมมา
        results = _OCR_READER.readtext(
            cropped,
            allowlist='0123456789,',
            detail=0,          # คืนแค่ข้อความ ไม่มี bbox
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

def send_discord_webhook(webhook_url, round_count, gold_this_round, total_gold, image_path=None):
    """
    ส่งข้อมูลสรุปผลประกอบการเข้า Discord Webhook พร้อมรูปภาพแคปหน้าจอจบเกม
    """
    if not webhook_url:
        print("⚠️ [Webhook] ไม่มี Webhook URL ในไฟล์ config")
        return

    if requests is None:
        print("❌ [Webhook] ไม่พบไลบรารี requests")
        return

    gold_this_round_str = f"{gold_this_round:,}" if isinstance(gold_this_round, int) else str(gold_this_round)
    total_gold_str = f"{total_gold:,}" if isinstance(total_gold, int) else str(total_gold)

    payload = {
        "embeds": [
            {
                "title": f"🎮 สรุปผลการเล่น CookieRun (ตาที่ {round_count})",
                "description": (
                    f"🏃 **เล่นไปแล้ว:** `{round_count}` ตา\n"
                    f"💰 **เงินที่ได้ตานี้:** `{gold_this_round_str}` เหรียญ\n"
                    f"🏦 **เงินรวมสะสมตั้งแต่เริ่ม:** `{total_gold_str}` เหรียญ"
                ),
                "color": 16766720  # สีทอง
            }
        ]
    }

    try:
        if image_path and os.path.exists(image_path):
            filename = os.path.basename(image_path)
            payload["embeds"][0]["image"] = {"url": f"attachment://{filename}"}
            with open(image_path, "rb") as f:
                files = {"file": (filename, f, "image/png")}
                response = requests.post(
                    webhook_url,
                    data={"payload_json": json.dumps(payload)},
                    files=files,
                    timeout=10
                )
        else:
            response = requests.post(webhook_url, json=payload, timeout=10)

        if response.status_code in [200, 204]:
            print(f"🔔 [Webhook] ส่งรายงานผลประกอบการตาที่ {round_count} เข้า Discord เรียบร้อยแล้ว!")
        else:
            print(f"⚠️ [Webhook] ส่งไม่สำเร็จ (Status Code: {response.status_code}): {response.text}")
    except Exception as e:
        print(f"❌ [Webhook Error] เกิดข้อผิดพลาด: {e}")

def check_boost(screen_img, templates_dir, boost, threshold=0.80):
    if screen_img is None:
        print("❌ [check_boost] screen_img is None")
        return False

    template_path = os.path.join(templates_dir, f"{boost}.png")
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    
    if template is None:
        print(f"❌ ไม่พบไฟล์รูป {template_path}")
        return False

    # 💡 เปลี่ยนเป็น Grayscale ช่วยลดปัญหาเรื่องสี/แสง/ฉากหลังเปลี่ยน
    gray_screen = cv2.cvtColor(screen_img, cv2.COLOR_BGR2GRAY)
    gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    # ===================================================
    # ⚡ STEP 1: Fast Check (เช็คเฉพาะโซน ROI)
    # ===================================================
    x1, y1 = 899, 700
    x2, y2 = 1348, 653
    
    ymin, ymax = min(y1, y2), max(y1, y2)
    xmin, xmax = min(x1, x2), max(x1, x2)

    roi = gray_screen[ymin:ymax, xmin:xmax]

    # ตรวจสอบว่ากรอบ ROI ใหญ่พอที่จะใส่ Template ได้หรือไม่
    if roi.shape[0] >= gray_template.shape[0] and roi.shape[1] >= gray_template.shape[1]:
        res_fast = cv2.matchTemplate(roi, gray_template, cv2.TM_CCOEFF_NORMED)
        _, max_val_fast, _, _ = cv2.minMaxLoc(res_fast)

        if max_val_fast >= threshold:
            print(f"✅ [Fast Check] ยืนยันตรงกับ Boost: {boost}! (ความเหมือน: {max_val_fast*100:.1f}%)")
            return True

    # ===================================================
    # 🔍 STEP 2: Fallback Search (หาทั้งหน้าจอ)
    # ===================================================
    res_full = cv2.matchTemplate(gray_screen, gray_template, cv2.TM_CCOEFF_NORMED)
    _, max_val_full, _, _ = cv2.minMaxLoc(res_full)

    if max_val_full >= threshold:
        print(f"✅ [Full Search] เจอ Boost: {boost} บนหน้าจอ! (ความเหมือน: {max_val_full*100:.1f}%)")
        return True
    
    print(f"❌ Boost ยังไม่ตรงกับ {boost} (ความเหมือนสูงสุดที่พบ: {max_val_full*100:.1f}% / ต้องการ: {threshold*100:.0f}%)")
    return False



def get_random_pos(x1, y1, x2, y2):
    """ฟังก์ชันช่วยสุ่มพิกัด X, Y ให้อยู่ภายในขอบเขตกรอบสี่เหลี่ยม"""
    rx = random.randint(min(x1, x2), max(x1, x2))
    ry = random.randint(min(y1, y2), max(y1, y2))
    return rx, ry

def preplay_process(adb_path, device_id, base_delay, user_config, templates_dir="templates"):
    print("\n🎬 --- เริ่มต้นฟังก์ชัน Preplay (เตรียมตัวก่อนเล่น) ---")
    time.sleep(2+base_delay)
    
    # 📌 Step 1: กดปุ่มเข้าหน้า Preplay จาก Loby
    x, y = get_random_pos(977, 850, 1400, 750)
    tap_button(adb_path, device_id, x, y)
    
    wait_time = 1. + base_delay
    print(f"⏳ [Step 1] กดเข้าหน้าเตรียมตัวเรียบร้อย -> รอ {wait_time:.2f} วินาที")
    time.sleep(wait_time)

    # 🔍 เช็คว่าผู้ใช้ต้องการ Boost หรือไม่
    is_boost_enabled = user_config.get("boost_mode", False)

    if is_boost_enabled:
        print("⚡ ผู้ใช้เลือกเปิดใช้งาน Boost -> เริ่มกระบวนการสุ่มและเลือก Boost...")

        # 📌 Step 2: กดปุ่มกล่องสุ่ม
        x, y = get_random_pos(590, 818, 740, 666)
        tap_button(adb_path, device_id, x, y)
        

        print(f"⏳ [Step 2] กดกล่องสุ่มเรียบร้อย -> รอ {wait_time:.2f} วินาที")
        time.sleep(wait_time)

        # 📌 Step 3: กดปุ่มปิด/ยืนยัน Pop-up สุ่ม
        x, y = get_random_pos(1340, 265, 1405, 221)
        tap_button(adb_path, device_id, x, y)
        
        # ⏳ รอให้ Pop-up จางหายไปสนิท
        print("⏳ รอ Pop-up ปิดสนิท (1.0 วินาที)...")
        time.sleep(1.0 + base_delay)

        # 📌 Step 5: กดปุ่มถัดไป (muit)
        time.sleep(1.0)
        x, y = get_random_pos(680, 771, 911, 701)
        tap_button(adb_path, device_id, x, y)
        print("🚀 กดปุ่มถัดไป (muit) เรียบร้อยแล้ว")
        count = 0
        while True:
            #เช็คผลลัพการสุ่ม
            time.sleep(5) #กันเช็คทันทีแล้วบัค
            current_screen = capture_screen(adb_path) # แคปหน้าจอใหม่
            
            if check_boost(current_screen, templates_dir, user_setup_boost.get("boost_name")):
                print("✅ สุ่มได้ Boost ตรงตามที่ต้องการแล้ว!")
                break
            else:
                print(f"⏳ Boost ยังไม่ตรง รอสุ่มใหม่...ครั้งที่ {count}/10")
                if count >=10:
                    # resolved = resolve_unknown_state(
                    # screen_img=current_screen,
                    # adb_path=adb_path,
                    # notfound_dir=notfound_dir,
                    # threshold=0.8
                    # )
                    print("รอสุ่มนานเกินไปอาจจะมีหน้าจออื่นบัง ให้กลับไป lobby หลักก่อน")
                    return False
                count += 1
        print("✨ --- จบการทำงานฟังก์ชัน preplay_process เรียบร้อยแล้ว --- \n")
        return True
        
    else:
        print("⏩ ผู้ใช้เลือก 'ไม่กด Boost' -> ข้ามขั้นตอนการสุ่มและเลือก Boost ทั้งหมด!")
        print("✨ --- จบการทำงานฟังก์ชัน preplay_process เรียบร้อยแล้ว --- \n")

        return True

    
    
def start2_process(adb_path, device_id, user_config):
    print("\n🎮 --- เริ่มต้นฟังก์ชัน Start2 (เตรียมเริ่มวิ่ง) ---")

    # 📌 Step 1: กดปุ่มเข้าสู่ด่าน (พิกัด: x1=930, y1=720 ถึง x2=1320, y2=800)
    x, y = get_random_pos(930, 720, 1320, 800)
    tap_button(adb_path, device_id, x, y)
    print("👉 กดปุ่มเริ่มวิ่งเรียบร้อยแล้ว!")

    # 📌 Step 2: เว้นระยะรอ 2 วินาที
    print("⏳ เว้นระยะรอ 2 วินาที...")
    time.sleep(4)

    # 📌 Step 3: เช็คเงื่อนไข Fast Start
    is_fast_start = user_config.get("fast_start", False)

    if is_fast_start:
        print("⚡ ผู้ใช้เลือก Fast Start -> สุ่มกดบริเวณปุ่ม Fast Start 10 ครั้ง...")
        
        # วนลูปกด 10 ครั้ง
        for i in range(1, 11):
            # พิกัด: x1=726, y1=345 ถึง x2=907, y2=513
            fx, fy = get_random_pos(726, 345, 907, 513)
            tap_button(adb_path, device_id, fx, fy)
            print(f"   └─ [{i}/10] กด Fast Start ที่พิกัด ({fx}, {fy})")
            time.sleep(0.3)
            
        print("⚡ กด Fast Start ย้ำครบ 10 ครั้งเรียบร้อย!")
    else:
        print("⏩ ข้ามการกด Fast Start (ผู้ใช้ไม่ได้เปิดใช้งาน)")
    
def crop_screen_area(image, bbox):
    """
    ตัดรูปภาพตามพื้นที่ (x1, y1, x2, y2)
    bbox: tuple (x1, y1, x2, y2)
    """
    x1, y1, x2, y2 = bbox
    # ปรับ min/max ให้ถูกต้องกรณีใส่พิกัดสลับกัน
    left, right = min(x1, x2), max(x1, x2)
    top, bottom = min(y1, y2), max(y1, y2)
    return image[top:bottom, left:right]    
    
def running_game(adb_path, templates_dir, notfound_dir, user_config, webhook_url="", total_runs=0, total_gold_accumulated=0):
    print("\n🏃 --- เริ่มต้นฟังก์ชัน Running Game (อยู่ในเกม) ---")
    
    start_time = time.time()
    timeout_limit = 7 * 60  # 7 นาที (420 วินาที)
    
    device_id = get_device_id(adb_path)
    is_round_2_enabled = user_config.get("round_2", False)
    has_relayed = False  # ตัวแปรกันไม่ให้กดผลัดซ้ำ
    munmot_count = 0    # ตัวแปรนับจำนวนครั้งการเคลียร์ munmot (ไม่เกิน 7 ครั้ง)
    loop_count = 0

# โหลด Template พร้อมเช็คไฟล์
    relay_path = os.path.join(templates_dir, "relay.png")
    result_path = os.path.join(templates_dir, "result.png")
    munmot_path = os.path.join(templates_dir, "munmot.png")

    relay_template = cv2.imread(relay_path, cv2.IMREAD_COLOR)
    result_template = cv2.imread(result_path, cv2.IMREAD_COLOR)
    munmot_template = cv2.imread(munmot_path, cv2.IMREAD_COLOR)




    # 🔍 ตรวจสอบความถูกต้องของไฟล์รูปภาพ
    if is_round_2_enabled and relay_template is None:
        print(f"⚠️ [เตือน] คุณเลือกเปิดใช้งาน 'ผลัด 2' แต่ระบบไม่พบไฟล์รูป: {relay_path}")
    
    if result_template is None:
        print(f"❌ [ข้อผิดพลาด] ไม่พบไฟล์รูปหน้าจบเกม: {result_path}")

    print(f"ℹ️ สถานะปุ่ม -> ผลัด 2: {is_round_2_enabled} | Fast Start: {user_config.get('fast_start', False)}")

    loop_count = 0

    while True:
        # 1. เช็ค Timeout 7 นาที
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout_limit:
            print(f"\n⚠️ เตือน: อยู่ในเกมนานเกิน 7 นาที ({elapsed_time:.0f} วินาที)!")
            print("🔄 สั่งการแก้สถานะติดค้างด้วย resolve_unknown_state...")
            
            current_screen = capture_screen(adb_path)
            resolve_unknown_state(
                screen_img=current_screen,
                adb_path=adb_path,
                notfound_dir=notfound_dir,
                threshold=0.8
            )
            break

        # 2. แคปหน้าจอปัจจุบัน
        current_screen = capture_screen(adb_path)
        if current_screen is None:
            time.sleep(1)
            continue

        loop_count += 1

        # 3. เช็ค "ผลัด 2" (ถ้าเปิดใช้งาน และยังไม่ได้กด)
        if is_round_2_enabled and not has_relayed and relay_template is not None:
            relay_crop = crop_screen_area(current_screen, (726, 345, 907, 513))
            
            # ถ้าขนาด Crop ใหญ่พอ ให้เทียบเฉพาะจุด ถ้าเล็กไปให้ fallback หาเรียงทั้งจอ
            if relay_crop.shape[0] >= relay_template.shape[0] and relay_crop.shape[1] >= relay_template.shape[1]:
                res_relay = cv2.matchTemplate(relay_crop, relay_template, cv2.TM_CCOEFF_NORMED)
            else:
                res_relay = cv2.matchTemplate(current_screen, relay_template, cv2.TM_CCOEFF_NORMED)
                
            _, max_val_relay, _, _ = cv2.minMaxLoc(res_relay)

            # แสดงสถานะสแกนทุกๆ 5 รอบ
            if loop_count % 5 == 0:
                print(f"🔍 [สแกนอยู่...] ความเหมือน relay.png: {max_val_relay*100:.1f}% (ต้องการ >= 75%)")

            if max_val_relay >= 0.75: # ปรับลดลงเป็น 0.75 เพื่อให้ติดง่ายขึ้น
                print(f"⚡ เจอหน้าต่าง 'ผลัด 2' (relay.png)! (ความเหมือน: {max_val_relay*100:.1f}%) -> กดปุ่ม")
                rx, ry = get_random_pos(726, 345, 907, 513)
                tap_button(adb_path, device_id, rx, ry)
                has_relayed = True  # บันทึกว่ากดผลัด 2 ไปแล้ว
                time.sleep(1.5)
                continue

        # ตรวจสอบเวลาเล่นสะสมเพื่อหยุดเกมเมื่อถึงเวลา playtime
        autojump = user_config.get("autojump", True)
        playtime = user_config.get("playtime", 180)
        elapsed_time = time.time() - start_time
        
        if elapsed_time >= playtime:
            print(f"⏱️ เวลาการเล่นถึงที่กำหนดแล้ว ({elapsed_time:.1f}/{playtime} วินาที) -> กำลังเรียกฟังก์ชัน stopgame...")
            # 3. ฟังก์ชั่น stopgame ให้กดปุ่มไปที่พิกัดนึงก่อน mx, my = get_random_pos(242, 586, 471, 382)
            mx, my = get_random_pos(999, 999, 999, 999)
            tap_button(adb_path, device_id, mx, my)
            # จากนั้น delay 1 + delay random 0.1-0.5 วิ
            delay_stop = 1.0 + random.uniform(0.1, 0.5)
            print(f"⏳ [stopgame] กดพิกัดเริ่มต้นสำเร็จ -> หน่วงเวลา {delay_stop:.2f} วินาที")
            time.sleep(delay_stop)
            
            # พอจบฟังก์ชั่นนี้อยากให้เข้า 4. เช็ค "หน้าจบเกม" (result.png)
            print("➡️ [stopgame] เสร็จสิ้น -> ข้ามไปตรวจเช็คหน้าจบเกม (result.png)")
            # โดยเราจะยังไม่ออกจากลูป แต่ในรอบถัดๆ ไป (หรือทันที) จะบังคับสแกนหน้าจบเกม
            # เพื่อความปลอดภัยและให้เข้าเงื่อนไขสแกนหน้าจบเกมทันที เราสามารถแคปภาพใหม่แล้วเช็คหน้าจบเกมได้เลย
            current_screen = capture_screen(adb_path)


        # 4. เช็ค "หน้าจบเกม" (result.png)
        if result_template is not None:
            result_crop = crop_screen_area(current_screen, (526, 515, 1055, 53))
            
            if result_crop.shape[0] >= result_template.shape[0] and result_crop.shape[1] >= result_template.shape[1]:
                res_result = cv2.matchTemplate(result_crop, result_template, cv2.TM_CCOEFF_NORMED)
            else:
                res_result = cv2.matchTemplate(current_screen, result_template, cv2.TM_CCOEFF_NORMED)
                
            _, max_val_result, _, _ = cv2.minMaxLoc(res_result)

            if loop_count % 5 == 0:
                print(f"🔍 [สแกนอยู่...] ความเหมือน result.png: {max_val_result*100:.1f}% (ต้องการ >= 75%)")

            if max_val_result >= 0.75:
                print(f"🏁 ตรวจพบหน้าจบเกม (result.png)! (ความเหมือน: {max_val_result*100:.1f}%) -> เริ่มทำขั้นตอนออกจากเกม...")
                
                # 🟢 1. นับจำนวนตาที่เล่นจบ
                total_runs += 1
                
                # 🟢 2. รอ 2 วินาทีเพื่อให้ตัวเลขเงินหน้ารายงานผลนิ่ง แล้วแคปภาพจบเกม
                time.sleep(2)
                end_screen = capture_screen(adb_path)
                if end_screen is None:
                    end_screen = current_screen

                # 🟢 3. บันทึกภาพหน้าจอจบเกม
                screenshot_path = "end_game_result.png"
                try:
                    cv2.imwrite(screenshot_path, end_screen)
                    print(f"📸 [Screenshot] บันทึกภาพหน้าจอจบเกมสำเร็จ: {screenshot_path}")
                except Exception as e:
                    print(f"⚠️ [Screenshot Error] ไม่สามารถบันทึกภาพหน้าจอจบเกมได้: {e}")
                    screenshot_path = None

                # 🟢 4. อ่านค่าเงินรางวัลที่ได้ในตานี้ (OCR) และคำนวณเงินสะสม
                gold_this_round, gold_str = extract_gold_amount(end_screen)
                total_gold_accumulated += gold_this_round

                print(f"📊 [สรุปผลรอบที่ {total_runs}] ได้รับเงินตานี้: {gold_str} | เงินรวมสะสมตั้งแต่เริ่ม: {total_gold_accumulated:,} เหรียญ")

                # 🟢 5. ส่งรายงานพร้อมภาพแคปหน้าจอเข้า Discord Webhook
                if webhook_url:
                    send_discord_webhook(
                        webhook_url=webhook_url,
                        round_count=total_runs,
                        gold_this_round=gold_this_round,
                        total_gold=total_gold_accumulated,
                        image_path=screenshot_path
                    )

                time.sleep(3)
                # Step A: กดปุ่มสุ่มบริเวณ (440, 740) ถึง (720, 810)
                x, y = get_random_pos(440, 740, 720, 810)
                tap_button(adb_path, device_id, x, y)
                print("👉 [1/3] กดปุ่มแรกเรียบร้อย -> รอ 3 วินาที")
                time.sleep(2)
                
                print("✨ --- จบเกมเรียบร้อยสมบูรณ์ --- \n")
                return total_runs, total_gold_accumulated

        # 5. เช็ค "หน้าต่าง munmot" (munmot.png) เฉพาะฟามมันบดเท่านั้นถ้าไม่ามให้ปิดด้วยข้อ 5.
        if autojump and munmot_template is not None and munmot_count < 7:
            munmot_crop = crop_screen_area(current_screen, (353, 512, 431, 495))

            if munmot_crop.shape[0] >= munmot_template.shape[0] and munmot_crop.shape[1] >= munmot_template.shape[1]:
                res_munmot = cv2.matchTemplate(munmot_crop, munmot_template, cv2.TM_CCOEFF_NORMED)
            else:
                res_munmot = cv2.matchTemplate(current_screen, munmot_template, cv2.TM_CCOEFF_NORMED)

            _, max_val_munmot, _, _ = cv2.minMaxLoc(res_munmot)

            if max_val_munmot >= 0.80:
                munmot_count += 1
                print(f"💥 ตรวจพบหน้าต่าง munmot.png! (ความเหมือน: {max_val_munmot*100:.1f}%) [ทำแล้ว {munmot_count}/7 ครั้ง]")
                max_jump = random.randint(12,15)
                # วนกดปุ่ม 16 ครั้ง ห่างกันครั้งละ 0.49 วินาที
                for i in range(1, max_jump):
                     mx, my = get_random_pos(242, 586, 471, 382)
                     tap_button(adb_path, device_id, mx, my)
                     delay_time = random.uniform(0.4, 0.67)

                     print(f"   └─ [{i}/{max_jump}] กดปุ่ม munmot ที่พิกัด ({mx}, {my}) (หน่วง {delay_time:.2f}s)")
                     time.sleep(delay_time)
                     mx, my = get_random_pos(1234, 359, 1349, 293)
                     tap_button(adb_path, device_id, mx, my)
                
                time.sleep(1.0)
                continue

        # รอ 0.01 วินาทีก่อนวนลูปสแกนใหม่
        time.sleep(0.05)

    return total_runs, total_gold_accumulated
    
    
    
    
# ==================== Main ====================
if __name__ == "__main__":
    config = load_config()
    
    if config:
        adb_path = config.get("adb_path", "adb")
        templates_dir = config.get("templates_dir", "templates")
        notfound_dir = config.get("notfound_dir", "notfound")
        anti_cheat_delay_min = config.get("anti_cheat_delay_min", 0.2)
        anti_cheat_delay_max = config.get("anti_cheat_delay_max", 1.0)
        webhook_url = config.get("discord_webhook_url", "")
        device_id = get_device_id(adb_path)
    
        delay = random.uniform(anti_cheat_delay_min, anti_cheat_delay_max)
        # 1. สั่งเปิดเกม
        start_game(config)
        
        user_setup_boost = setup_boost.get_user_configuration()
        
        # 🟢 ตัวแปรสำหรับจำค่าสะสมการรัน (State Tracking across games)
        total_runs = 0
        total_gold_accumulated = 0

        # 2. วนลูปเช็คหน้า Loby
        while True:
            current_screen = capture_screen(adb_path)
            
            # เช็คว่าอยู่หน้า Loby หรือไม่
            if check_loby_state(current_screen, templates_dir):
                print("🎮 เข้าหน้าหลัก (Loby) เรียบร้อย! เริ่มทำขั้นตอนถัดไป...")
                time.sleep(3 + delay) #รอให้โหลดอะไรเสร็จกันเร็วไป
                # 2
                check_state_preplay = preplay_process(
                    adb_path=adb_path, 
                    device_id=device_id, 
                    base_delay=delay, 
                    user_config=user_setup_boost
                )
                if not check_state_preplay :
                    print('กลับไปหน้าหลัก')
                    continue
                
                user_setup_boost["autojump"] = config.get("autojump", True)
                user_setup_boost["playtime"] = config.get("playtime", 180)

                start2_process(adb_path=adb_path, device_id=device_id, user_config=user_setup_boost)
                total_runs, total_gold_accumulated = running_game(
                    adb_path=adb_path,
                    templates_dir=templates_dir,
                    notfound_dir=notfound_dir,
                    user_config=user_setup_boost,
                    webhook_url=webhook_url,
                    total_runs=total_runs,
                    total_gold_accumulated=total_gold_accumulated
                )

            else:
                print("🔄 ไม่ใช่หน้า Loby -> เข้าสู่โหมดสแกนหาปุ่มเคลียร์ Pop-up (notfound)...")
                
                # วนสแกนหารูปในโฟลเดอร์ notfound/ แล้วกดออกให้อัตโนมัติ
                resolved = resolve_unknown_state(
                    screen_img=current_screen,
                    adb_path=adb_path,
                    notfound_dir=notfound_dir,
                    threshold=0.8
                )
                
                if resolved:
                    time.sleep(2)  # ถ้าเจอปุ่มและกดไปแล้ว ให้หยุดรอ 2 วินาทีให้ป๊อปอัปจาง
                else:
                    time.sleep(1)