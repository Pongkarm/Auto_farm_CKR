# 🌾 Auto_farm_CKR

> **Code Wizard:** Freya Taylor  
> **Status:** Running on Pure Coffee & Dark Magic ☕✨  
> สคริปต์ช่วยฟาร์มอัตโนมัติสำหรับ CookieRun (CKR)

---

## 🚀 วิธีการใช้งาน (Getting Started)

1. **ตั้งค่าไฟล์การทำงาน:**  
   เปิดไฟล์ [Config.json](file:///Users/pongkarm/Downloads/Auto_farm_CKR/Pongkarmm_Coockierun_GOD/Config.json) และตั้งค่าตามต้องการ (ดูรายละเอียดที่ [การใช้งานไฟล์ config](#การใช้งานไฟล์config))

2. **เริ่มการทำงาน:**  
   เปิดโฟลเดอร์ `Pongkarmm_Coockierun_GOD` แล้วรันไฟล์หลักด้วยคำสั่ง:
   ```bash
   python Cookie.py
   ```

---

## การใช้งานไฟล์config

สามารถตั้งค่าไฟล์ [Config.json](file:///Users/pongkarm/Downloads/Auto_farm_CKR/Pongkarmm_Coockierun_GOD/Config.json) ได้ดังนี้:

### ⚙️ config_summary

| Key | Type | Description |
| :--- | :--- | :--- |
| `adb_path` | string | ที่อยู่ไฟล์ `adb.exe` ในเครื่องคอมพิวเตอร์ของคุณ |
| `discord_webhook_url` | string | URL Webhook ของ Discord สำหรับส่งรายงานผลฟาร์ม |
| `use_discord_webhook` | boolean | เปิด (`true`) หรือ ปิด (`false`) การส่งรายงานไปยัง Discord |
| `target_package` | string | Package name ของเกม |
| `target_activity` | string | Activity name สำหรับเริ่มต้นเปิดเกมผ่าน ADB |
| `templates_dir` | string | โฟลเดอร์เก็บเทมเพลตภาพสำหรับการตรวจจับหน้าจอหลัก (`templates`) |
| `notfound_dir` | string | โฟลเดอร์เก็บรูปภาพปุ่มแก้สถานะบอทติดขัด/ป๊อปอัปแจ้งเตือน (`notfound`) |
| `rounds_per_set` | integer | จำนวนรอบที่ต้องการฟาร์ม เมื่อครบกำหนดจะทำการ**ปิดหน้าต่าง Terminal ทันที** |
| `anti_cheat_delay_min` / `max` | float | หน่วงเวลาขั้นต่ำและสูงสุด (วินาที) เพื่อป้องกันการตรวจจับบอท |
| `autojump` | boolean | เปิด/ปิดการกระโดดหลบอัตโนมัติในส่วนของห้องมันบด |
| `playtime` | integer | เวลาที่ใช้เล่นต่อรอบ (วินาที) เมื่อหมดเวลาบอทจะสั่งกดยอมแพ้เพื่อจบตาเก็บเหรียญ |
| `auto_setup` | boolean | เปิด (`true`) เพื่อข้ามคำถามตอนเริ่มสคริปต์ และดึงการตั้งค่าด้านล่างไปใช้โดยอัตโนมัติ |
| `fast_start` | boolean | เปิดใช้ความเร็ว Fast Start ตอนเริ่มวิ่งรอบการเล่น |
| `round_2` | boolean | เปิดใช้งานการกดวิ่งต่อในรอบที่สอง (ผลัด 2) |
| `boost_name` | string | ชื่อประเภท Boost ที่สุ่มนำมาใช้ (ระบุ `"0"` เพื่อปิดการใช้งาน Boost) |
