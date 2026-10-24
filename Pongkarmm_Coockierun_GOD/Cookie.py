import sys
import os

# ปรับ Working Directory ให้ชี้ไปที่โฟลเดอร์ของตัวโปรแกรมเสมอ
# (ป้องกัน Error หา Config.json หรือ templates ไม่เจอ เวลาดับเบิ้ลคลิก .exe หรือ Shortcut)
if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))
else:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import random
import time
import signal

# นำเข้าฟังก์ชันจากไฟล์โมดูลย่อย
from adb_utils import get_device_id, start_game
from image_utils import capture_screen
from game_flows import (
    check_loby_state,
    resolve_unknown_state,
    preplay_process,
    start2_process,
    running_game
)
import setup_boost

# โหลดไฟล์ Config.json
def load_config(config_path="Config.json"):
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            print("✅ โหลดไฟล์ Config.json สำเร็จ")
            return config
    except FileNotFoundError:
        print("❌ ไม่พบไฟล์ Config.json กรุณาตรวจสอบตำแหน่งไฟล์")
        return None

# ==================== Main ====================
if __name__ == "__main__":
    config = load_config()
    
    if config:
        adb_path = config.get("adb_path", "adb")
        templates_dir = config.get("templates_dir", "templates")
        notfound_dir = config.get("notfound_dir", "notfound")
        anti_cheat_delay_min = config.get("anti_cheat_delay_min", 0.2)
        anti_cheat_delay_max = config.get("anti_cheat_delay_max", 1.0)
        
        # 🟢 ดึงค่าใช้ Discord Webhook จาก config
        use_discord_webhook = config.get("use_discord_webhook", False)
        webhook_url = config.get("discord_webhook_url", "") if use_discord_webhook else ""
        
        # 🟢 ดึงจำนวนรอบทั้งหมดในเซ็ต
        rounds_per_set = config.get("rounds_per_set", 999)
        
        device_id = get_device_id(adb_path)
    
        delay = random.uniform(anti_cheat_delay_min, anti_cheat_delay_max)
        # 1. สั่งเปิดเกม
        start_game(config)
        
        user_setup_boost = setup_boost.get_user_configuration(config)
        
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
                
                check_state_preplay = preplay_process(
                    adb_path=adb_path, 
                    device_id=device_id, 
                    base_delay=delay, 
                    user_config=user_setup_boost,
                    templates_dir=templates_dir
                )
                if not check_state_preplay:
                    print('กลับไปหน้าหลัก')
                    continue
                
                user_setup_boost["autojump"] = config.get("autojump", False)
                user_setup_boost["playtime"] = config.get("playtime", 420)

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
                
                # 🟢 เช็คเมื่อเล่นจบแต่ละรอบว่าครบจำนวน rounds_per_set หรือยัง
                if total_runs >= rounds_per_set:
                    print(f"\n🎉 เล่นครบตามจำนวนรอบที่กำหนดแล้ว: {total_runs}/{rounds_per_set} รอบ")
                    print("🛑 กำลังปิดโปรแกรมและหน้าต่าง Terminal...")
                    time.sleep(2)
                    try:
                        if os.name == 'nt':
                            os.system(f"taskkill /F /PID {os.getppid()}")
                        else:
                            os.kill(os.getppid(), signal.SIGKILL)
                    except Exception as e:
                        print(f"⚠️ ไม่สามารถปิด Terminal ได้โดยตรง: {e}")
                    sys.exit(0)

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