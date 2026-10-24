@echo off
chcp 65001 >nul
echo ========================================================
echo        กำลังสร้างไฟล์ Cookie.exe ด้วย PyInstaller
echo ========================================================

:: 1. ติดตั้ง Library ที่จำเป็น
echo [1/3] ตรวจสอบและติดตั้ง dependencies จาก requirements.txt...
pip install -r requirements.txt

:: 2. สั่ง Compile ด้วย PyInstaller แบบโฟลเดอร์ (--onedir)
echo [2/3] กำลัง Compile Cookie.py เป็น .exe...
pyinstaller --noconfirm --onedir --console --name "Cookie" ^
    --hidden-import "easyocr" ^
    --hidden-import "torch" ^
    --hidden-import "torchvision" ^
    Cookie.py

:: 3. คัดลอกโฟลเดอร์ Assets และ Config.json ไปไว้ข้างๆ Cookie.exe
echo [3/3] กำลังเตรียมไฟล์ Config และ Assets ในโฟลเดอร์ dist\Cookie...
if not exist "dist\Cookie" mkdir "dist\Cookie"
copy /Y "Config.json" "dist\Cookie\Config.json"
xcopy /E /I /Y "templates" "dist\Cookie\templates"
xcopy /E /I /Y "check_boost" "dist\Cookie\check_boost"
xcopy /E /I /Y "notfound" "dist\Cookie\notfound"

echo ========================================================
echo  ✅ สร้างไฟล์ .exe สำเร็จเรียบร้อย!
echo  📁 โฟลเดอร์ผลลัพธ์อยู่ที่: dist\Cookie\
echo  ⚙️ คุณสามารถเปิดเข้าไปแก้ไข Config.json และดับเบิ้ลคลิก Cookie.exe ใช้งานได้ทันที
echo ========================================================
pause
