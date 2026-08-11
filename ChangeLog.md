# 🚀 Release v1.0.0 - Major Refactoring & Auto-Shutdown Update

## 🛠️ 1. Config & Discord Integration
* **Discord Webhook Toggle:** เชื่อมระบบ flag `use_discord_webhook` ใน `Config.json` ให้ใช้งานได้จริง (หากเป็น `false` จะข้ามการส่ง Webhook)
* **Clean Config:** ลบตัวแปร `boost_mode` ที่ซ้ำซ้อน โดยเปลี่ยนมาเช็กจาก `boost_name` แทน (ตั้งค่าเป็น `"0"` หากต้องการปิด Boost)

## 🛑 2. Auto-Shutdown System
* **Rounds Limitation (`rounds_per_set`):** เพิ่มเงื่อนไขการหยุดรันเมื่อทำงานครบจำนวนรอบที่กำหนด ระบบจะส่งคำสั่ง Kill Process ปิดหน้าต่าง Terminal ทันที (รองรับทั้ง Windows และ macOS)

## 🏗️ 3. Code Base Refactoring (Modularization)
แยกโค้ดหลักออกจากกัน เพื่อให้อ่านง่าย สเกลง่าย และดูแลรักษาสะดวก:
* `Cookie.py`: Main Execution Loop ควบคุมภาพรวมระบบ
* `game_flows.py`: ตรรกะของเกม (Lobby, Preplay, Running, Resolve Unknown State)
* `adb_utils.py`: ระบบควบคุมพอร์ตและคำสั่ง ADB (Tap / Swipe)
* `image_utils.py`: จัดการงานแคปภาพหน้าจอและการ Crop รูปภาพ
* `ocr_helper.py`: ควบคุม EasyOCR อ่านค่ารางวัล/เงินหลังจบเกม
* `discord_helper.py`: โมดูลย่อยสำหรับส่ง Notification เข้า Discord Webhook

## ⚡ 4. Setup & Boost Options (`setup_boost.py`)
* **Auto Setup Mode:** เพิ่มฟีเจอร์ `auto_setup` ใน Config (หากเป็น `true` จะข้ามคำถามตอนเริ่มระบบ และดึงค่าไปเริ่มสแกนเกมทันที)
* **Streamlined Menu:** ยุบรวมการตั้งค่า Boost เข้าเป็นตัวเลือกตัวเลข พร้อมเพิ่มหมายเลข `[0]` เพื่อข้ามการใช้ Boost อย่างรวดเร็ว