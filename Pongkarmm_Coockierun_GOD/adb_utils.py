import subprocess
import time
import random

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

def tap_button(adb_path, device_id, x, y):
    rx = x + random.randint(-3, 3)
    ry = y + random.randint(-3, 3)
    
    cmd = f'"{adb_path}" -s {device_id} shell input tap {rx} {ry}'
    subprocess.run(cmd, shell=True)
    print(f"👆 [Click] กด/Pop-up ที่พิกัด: ({rx}, {ry})")
