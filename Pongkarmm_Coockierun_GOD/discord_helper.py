import os
import json
import requests

def send_discord_webhook(webhook_url, round_count, gold_this_round, total_gold, image_path=None):
    """
    ส่งข้อมูลสรุปผลประกอบการเข้า Discord Webhook พร้อมรูปภาพแคปหน้าจอจบเกม
    """
    if not webhook_url:
        print("⚠️ [Webhook] ไม่มี Webhook URL ในไฟล์ config")
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
