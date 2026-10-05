import os
import time
import random
import cv2
import numpy as np

# นำเข้าฟังก์ชันช่วยเหลือจากโมดูลอื่นๆ
from adb_utils import get_device_id, tap_button
from image_utils import capture_screen, crop_screen_area, get_random_pos
from ocr_helper import extract_gold_amount
from discord_helper import send_discord_webhook

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

    if max_val_full >= 0.90:
        print(f"✅ [Full Search] เจอหน้า Loby บนหน้าจอ! (ความเหมือน: {max_val_full*100:.1f}%)")
        return True
    
    print(f"❌ ไม่อยู่หน้า Loby (ความเหมือนสูงสุดแค่: {max_val_full*100:.1f}%)")
    return False

# 7. ฟังก์ชันจัดการหน้าแปลก / เคลียร์ Pop-up (วนลูปเช็ครูปในโฟลเดอร์ notfound)
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

# 8. ฟังก์ชันตรวจเช็คสถานะ Boost สุ่ม
def check_boost(screen_img, templates_dir, boost, threshold=0.80):
    if screen_img is None:
        print("❌ [check_boost] screen_img is None")
        return False

    template_path = os.path.join(templates_dir, f"{boost}.png")
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    
    if template is None:
        print(f"❌ ไม่พบไฟล์รูป {template_path}")
        return False

    gray_screen = cv2.cvtColor(screen_img, cv2.COLOR_BGR2GRAY)
    gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    x1, y1 = 899, 700
    x2, y2 = 1348, 653
    
    ymin, ymax = min(y1, y2), max(y1, y2)
    xmin, xmax = min(x1, x2), max(x1, x2)

    roi = gray_screen[ymin:ymax, xmin:xmax]

    if roi.shape[0] >= gray_template.shape[0] and roi.shape[1] >= gray_template.shape[1]:
        res_fast = cv2.matchTemplate(roi, gray_template, cv2.TM_CCOEFF_NORMED)
        _, max_val_fast, _, _ = cv2.minMaxLoc(res_fast)

        if max_val_fast >= threshold:
            print(f"✅ [Fast Check] ยืนยันตรงกับ Boost: {boost}! (ความเหมือน: {max_val_fast*100:.1f}%)")
            return True

    res_full = cv2.matchTemplate(gray_screen, gray_template, cv2.TM_CCOEFF_NORMED)
    _, max_val_full, _, _ = cv2.minMaxLoc(res_full)

    if max_val_full >= threshold:
        print(f"✅ [Full Search] เจอ Boost: {boost} บนหน้าจอ! (ความเหมือน: {max_val_full*100:.1f}%)")
        return True
    
    print(f"❌ Boost ยังไม่ตรงกับ {boost} (ความเหมือนสูงสุดที่พบ: {max_val_full*100:.1f}% / ต้องการ: {threshold*100:.0f}%)")
    return False

# 9. ฟังก์ชันเตรียมความพร้อมก่อนวิ่ง (Preplay)
def preplay_process(adb_path, device_id, base_delay, user_config, templates_dir="templates"):
    print("\n🎬 --- เริ่มต้นฟังก์ชัน Preplay (เตรียมตัวก่อนเล่น) ---")
    time.sleep(2+base_delay)
    
    x, y = get_random_pos(977, 850, 1400, 750)
    tap_button(adb_path, device_id, x, y)
    
    wait_time = 1. + base_delay
    print(f"⏳ [Step 1] กดเข้าหน้าเตรียมตัวเรียบร้อย -> รอ {wait_time:.2f} วินาที")
    time.sleep(wait_time)

    is_boost_enabled = user_config.get("boost_mode", False)

    if is_boost_enabled:
        print("⚡ ผู้ใช้เลือกเปิดใช้งาน Boost -> เริ่มกระบวนการสุ่มและเลือก Boost...")

        x, y = get_random_pos(590, 818, 740, 666)
        tap_button(adb_path, device_id, x, y)

        print(f"⏳ [Step 2] กดกล่องสุ่มเรียบร้อย -> รอ {wait_time:.2f} วินาที")
        time.sleep(wait_time)

        x, y = get_random_pos(1340, 265, 1405, 221)
        tap_button(adb_path, device_id, x, y)
        
        print("⏳ รอ Pop-up ปิดสนิท (1.0 วินาที)...")
        time.sleep(1.0 + base_delay)

        time.sleep(1.0)
        x, y = get_random_pos(680, 771, 911, 701)
        tap_button(adb_path, device_id, x, y)
        print("🚀 กดปุ่มถัดไป (muit) เรียบร้อยแล้ว")
        count = 0
        while True:
            time.sleep(5)
            current_screen = capture_screen(adb_path)
            
            boost_name = user_config.get("boost_name")
            if check_boost(current_screen, templates_dir, boost_name):
                print("✅ สุ่มได้ Boost ตรงตามที่ต้องการแล้ว!")
                break
            else:
                print(f"⏳ Boost ยังไม่ตรง รอสุ่มใหม่...ครั้งที่ {count}/10")
                if count >=10:
                    print("รอสุ่มนานเกินไปอาจจะมีหน้าจออื่นบัง ให้กลับไป lobby หลักก่อน")
                    return False
                count += 1
        print("✨ --- จบการทำงานฟังก์ชัน preplay_process เรียบร้อยแล้ว --- \n")
        return True
        
    else:
        print("⏩ ผู้ใช้เลือก 'ไม่กด Boost' -> ข้ามขั้นตอนการสุ่มและเลือก Boost ทั้งหมด!")
        print("✨ --- จบการทำงานฟังก์ชัน preplay_process เรียบร้อยแล้ว --- \n")
        return True

# 10. ฟังก์ชันเริ่มวิ่ง (Start2)
def start2_process(adb_path, device_id, user_config):
    print("\n🎮 --- เริ่มต้นฟังก์ชัน Start2 (เตรียมเริ่มวิ่ง) ---")

    x, y = get_random_pos(930, 720, 1320, 800)
    tap_button(adb_path, device_id, x, y)
    print("👉 กดปุ่มเริ่มวิ่งเรียบร้อยแล้ว!")

    print("⏳ เว้นระยะรอ 2 วินาที...")
    time.sleep(4)

    is_fast_start = user_config.get("fast_start", False)

    if is_fast_start:
        print("⚡ ผู้ใช้เลือก Fast Start -> สุ่มกดบริเวณปุ่ม Fast Start 10 ครั้ง...")
        
        for i in range(1, 11):
            fx, fy = get_random_pos(726, 345, 907, 513)
            tap_button(adb_path, device_id, fx, fy)
            print(f"   └─ [{i}/10] กด Fast Start ที่พิกัด ({fx}, {fy})")
            time.sleep(0.3)
            
        print("⚡ กด Fast Start ย้ำครบ 10 ครั้งเรียบร้อย!")
    else:
        print("⏩ ข้ามการกด Fast Start (ผู้ใช้ไม่ได้เปิดใช้งาน)")

# 11. ฟังก์ชันวนลูปในหน้าจอการเล่นเกม (Running Game)
def running_game(adb_path, templates_dir, notfound_dir, user_config, webhook_url="", total_runs=0, total_gold_accumulated=0):
    print("\n🏃 --- เริ่มต้นฟังก์ชัน Running Game (อยู่ในเกม) ---")
    
    start_time = time.time()
    timeout_limit = 7 * 60  # 7 นาที (420 วินาที)
    
    device_id = get_device_id(adb_path)
    is_round_2_enabled = user_config.get("round_2", False)
    has_relayed = False  # ตัวแปรกันไม่ให้กดผลัดซ้ำ
    munmot_count = 0    # ตัวแปรนับจำนวนครั้งการเคลียร์ munmot (ไม่เกิน 7 ครั้ง)
    loop_count = 0

    relay_path = os.path.join(templates_dir, "relay.png")
    result_path = os.path.join(templates_dir, "result.png")
    munmot_path = os.path.join(templates_dir, "munmot.png")

    relay_template = cv2.imread(relay_path, cv2.IMREAD_COLOR)
    result_template = cv2.imread(result_path, cv2.IMREAD_COLOR)
    munmot_template = cv2.imread(munmot_path, cv2.IMREAD_COLOR)

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
            
            if relay_crop.shape[0] >= relay_template.shape[0] and relay_crop.shape[1] >= relay_template.shape[1]:
                res_relay = cv2.matchTemplate(relay_crop, relay_template, cv2.TM_CCOEFF_NORMED)
            else:
                res_relay = cv2.matchTemplate(current_screen, relay_template, cv2.TM_CCOEFF_NORMED)
                
            _, max_val_relay, _, _ = cv2.minMaxLoc(res_relay)

            if loop_count % 5 == 0:
                print(f"🔍 [สแกนอยู่...] ความเหมือน relay.png: {max_val_relay*100:.1f}% (ต้องการ >= 75%)")

            if max_val_relay >= 0.75:
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
            mx, my = get_random_pos(1467, 66, 1512, 22)
            tap_button(adb_path, device_id, mx, my)
            delay_stop = 1.0 + random.uniform(0.1, 0.5)
            time.sleep(delay_stop)
            
            mx, my = get_random_pos(630, 571, 932, 484)
            tap_button(adb_path, device_id, mx, my)
            delay_stop = 1.0 + random.uniform(0.1, 0.5)
            time.sleep(delay_stop)
            
            mx, my = get_random_pos(640, 522, 948, 434)
            tap_button(adb_path, device_id, mx, my)
        
            print(f"⏳ [stopgame] กดพิกัดเริ่มต้นสำเร็จ -> หน่วงเวลา {delay_stop:.2f} วินาที")
            time.sleep(0.99 + delay_stop)
            
            print("➡️ [stopgame] เสร็จสิ้น -> ข้ามไปตรวจเช็คหน้าจบเกม (result.png)")
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
                
                total_runs += 1
                
                time.sleep(2)
                end_screen = capture_screen(adb_path)
                if end_screen is None:
                    end_screen = current_screen

                screenshot_path = "end_game_result.png"
                try:
                    cv2.imwrite(screenshot_path, end_screen)
                    print(f"📸 [Screenshot] บันทึกภาพหน้าจอจบเกมสำเร็จ: {screenshot_path}")
                except Exception as e:
                    print(f"⚠️ [Screenshot Error] ไม่สามารถบันทึกภาพหน้าจอจบเกมได้: {e}")
                    screenshot_path = None

                gold_this_round, gold_str = extract_gold_amount(end_screen)
                total_gold_accumulated += gold_this_round

                print(f"📊 [สรุปผลรอบที่ {total_runs}] ได้รับเงินตานี้: {gold_str} | เงินรวมสะสมตั้งแต่เริ่ม: {total_gold_accumulated:,} เหรียญ")

                if webhook_url:
                    send_discord_webhook(
                        webhook_url=webhook_url,
                        round_count=total_runs,
                        gold_this_round=gold_this_round,
                        total_gold=total_gold_accumulated,
                        image_path=screenshot_path
                    )

                time.sleep(3)
                x, y = get_random_pos(440, 740, 720, 810)
                tap_button(adb_path, device_id, x, y)
                print("👉 [1/3] กดปุ่มแรกเรียบร้อย -> รอ 3 วินาที")
                time.sleep(2)
                
                print("✨ --- จบเกมเรียบร้อยสมบูรณ์ --- \n")
                return total_runs, total_gold_accumulated

        # 5. เช็ค "หน้าต่าง munmot" (munmot.png)
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

        time.sleep(0.05)

    return total_runs, total_gold_accumulated
