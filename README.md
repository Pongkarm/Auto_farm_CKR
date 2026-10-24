# 🌾 Auto_farm_CKR

> **Code Wizard:** Freya Taylor  
> **Status:** Running on Pure Coffee & Dark Magic ☕✨  
> สคริปต์ช่วยฟาร์มอัตโนมัติสำหรับ CookieRun (CKR)

---

## 📚 รายการไลบรารีทั้งหมดที่ใช้ในโปรเจกต์ (Libraries & Dependencies)

ตารางแสดงไลบรารีที่จำเป็น พร้อมหน้าที่การทำงานในโปรเจกต์:

| ชื่อไลบรารี (Package) | หน้าที่ในโปรเจกต์นี้ |
| :--- | :--- |
| **`opencv-python`** (`cv2`) | จัดการและประมวลผลรูปภาพ ทำ Image Template Matching ตรวจจับหน้าจอเกมและปุ่มต่างๆ |
| **`numpy`** | จัดการ Array ตัวเลขและข้อมูลพิกเซลของภาพร่วมกับ OpenCV |
| **`easyocr`** | โมเดล AI Deep Learning OCR ใช้อ่านจำนวนเหรียญ/เงินที่ฟาร์มได้จากภาพสรุปจบเกม (รันบน PyTorch) |
| **`requests`** | เชื่อมต่อเครือข่ายสำหรับส่งรายงานสถิติการฟาร์มผ่าน Discord Webhook |
| **`pytesseract`** | เครื่องมือ OCR ทางเลือก (ใช้ในสคริปต์ทดสอบ `test_ocr.py`) |
| **`pillow`** (`PIL`) | จัดการเปิดและแปลงไฟล์รูปภาพสำหรับระบบ OCR |
| **`pyinstaller`** | เครื่องมือสำหรับแปลงสคริปต์ Python เป็นไฟล์ `.exe` สำหรับใช้งานบน Windows |

---

## 🛠️ ขั้นตอนการติดตั้งและเตรียม Environment (แยกตามระบบปฏิบัติการ)

เพื่อป้องกันปัญหาเวอร์ชันไลบรารีชนกัน แนะนำให้สร้างสภาพแวดล้อมจำลอง (**Virtual Environment / venv**) ก่อนติดตั้งไลบรารีเสมอ:

### 🪟 สำหรับผู้ใช้งาน Windows

เปิด **Command Prompt (CMD)** หรือ **PowerShell** แล้วพิมพ์ตามลำดับ:

```bat
:: 1. เข้าโฟลเดอร์โปรเจกต์
cd Auto_farm_CKR-main\Pongkarmm_Coockierun_GOD

:: 2. สร้าง Virtual Environment ชื่อ 'venv'
python -m venv venv

:: 3. เปิดใช้งาน (Activate) Virtual Environment
:: ถ้าใช้ Command Prompt:
call venv\Scripts\activate
:: ถ้าใช้ PowerShell:
.\venv\Scripts\Activate.ps1

:: 4. อัปเดต pip และติดตั้งไลบรารีทั้งหมด
python -m pip install --upgrade pip
pip install -r requirements.txt
```

*(หรือหากไม่ต้องการใช้ requirements.txt สามารถพิมพ์คำสั่งรวมติดตั้งโดยตรงได้ทันที:)*
```bat
pip install opencv-python numpy easyocr requests pytesseract pillow pyinstaller
```

---

### 🍎 สำหรับผู้ใช้งาน macOS / Linux

เปิด **Terminal** แล้วพิมพ์ตามลำดับ:

```bash
# 1. เข้าโฟลเดอร์โปรเจกต์
cd Auto_farm_CKR-main/Pongkarmm_Coockierun_GOD

# 2. สร้าง Virtual Environment ชื่อ 'venv'
python3 -m venv venv

# 3. เปิดใช้งาน (Activate) Virtual Environment
source venv/bin/activate

# 4. อัปเดต pip และติดตั้งไลบรารีทั้งหมด
pip install --upgrade pip
pip install -r requirements.txt
```

*(หรือคำสั่งรวมติดตั้งแบบบรรทัดเดียว:)*
```bash
pip install opencv-python numpy easyocr requests pytesseract pillow pyinstaller
```

---

### 🔍 คำสั่งตรวจสอบความพร้อมของไลบรารี (Verification Command)

เมื่อติดตั้งเสร็จแล้ว คุณสามารถรันคำสั่งบรรทัดเดียวนี้เพื่อเช็คว่าติดตั้งทุกตัวครบถ้วนถูกต้องหรือไม่:

- **Windows:**
  ```bat
  python -c "import cv2, numpy, easyocr, requests, PIL, pytesseract; print('✅ ทุกไลบรารีติดตั้งครบและพร้อมใช้งาน!')"
  ```
- **macOS / Linux:**
  ```bash
  python3 -c "import cv2, numpy, easyocr, requests, PIL, pytesseract; print('✅ ทุกไลบรารีติดตั้งครบและพร้อมใช้งาน!')"
  ```

---

## 🚀 วิธีการเริ่มใช้งาน (Getting Started)

### 1. ตั้งค่าไฟล์การทำงาน
เปิดไฟล์ [Config.json](file:///Users/pongkarm/Downloads/Auto_farm_CKR-main/Pongkarmm_Coockierun_GOD/Config.json) และตั้งค่าตามต้องการ โดยเฉพาะพาธ `adb_path` ให้ชี้ไปยังโปรแกรมจำลอง Android (เช่น LDPlayer) ของคุณ (ดูรายละเอียดที่ [การใช้งานไฟล์ config](#การใช้งานไฟล์config))

### 2. เริ่มการทำงาน

#### 🪟 สำหรับระบบ Windows
เลือกใช้งานได้ตามสะดวก:
- **วิธีที่ 1 (ดับเบิ้ลคลิกผ่าน .bat):** เข้าโฟลเดอร์ `Pongkarmm_Coockierun_GOD` แล้วดับเบิ้ลคลิกไฟล์ `run_win.bat`
- **วิธีที่ 2 (แปลงเป็นไฟล์ .exe):**
  1. ดับเบิ้ลคลิกที่ไฟล์ `build_exe.bat` เพื่อคอมไพล์เป็น `.exe`
  2. เมื่อเสร็จสิ้น จะได้โฟลเดอร์ `dist\Cookie\` ซึ่งมีไฟล์ `Cookie.exe` สามารถดับเบิ้ลคลิกใช้งานได้ทันที (สามารถแก้ไข `Config.json` ในโฟลเดอร์นั้นได้ตลอดเวลา)
- **วิธีที่ 3 (ผ่าน Command Prompt / Terminal):**
  ```bash
  python Cookie.py
  ```

#### 🍎 สำหรับระบบ macOS
- **ดับเบิ้ลคลิกเปิดโปรแกรม:** เข้าโฟลเดอร์ `Pongkarmm_Coockierun_GOD` แล้วดับเบิ้ลคลิกที่ไฟล์ `run_mac.command`
- **หรือรันผ่าน Terminal:**
  ```bash
  python3 Cookie.py
  ```

---

## ⚙️ การใช้งานไฟล์ config

สามารถตั้งค่าไฟล์ [Config.json](file:///Users/pongkarm/Downloads/Auto_farm_CKR-main/Pongkarmm_Coockierun_GOD/Config.json) ได้ดังนี้:

### config_summary

| Key | Type | Description |
| :--- | :--- | :--- |
| `adb_path` | string | ที่อยู่ไฟล์ `adb.exe` ในเครื่องคอมพิวเตอร์ของคุณ (เช่น `C:\\LDPlayer\\LDPlayer9\\adb.exe`) |
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
