def get_user_configuration():
    # ANSI Color Codes
    RESET, BOLD = "\033[0m", "\033[1m"
    CYAN, GREEN, YELLOW = "\033[96m", "\033[92m", "\033[93m"
    MAGENTA, RED, BLUE = "\033[95m", "\033[91m", "\033[94m"

    # Header
    print(f"\n{CYAN}═" * 58)
    print(f"{BOLD}{MAGENTA}  ✨ GAME SETUP CONFIGURATION ✨".center(66))
    print(f"{CYAN}═" * 58 + f"{RESET}\n")

    # 1. ถาม Fast Start
    while True:
        ans = input(f"{YELLOW}▶ กด Fast Start ไหม? {BOLD}(y/n):{RESET} ").strip().lower()
        if ans in ['y', 'yes']:
            fast_start = True
            break
        elif ans in ['n', 'no']:
            fast_start = False
            break
        print(f"  {RED}✖ พิมพ์ผิด! กรุณาตอบเฉพาะ 'y' หรือ 'n' เท่านั้น{RESET}")

    # 2. ถาม ผลัด 2
    while True:
        ans = input(f"{YELLOW}▶ กด ผลัด 2 ไหม? {BOLD}(y/n):{RESET} ").strip().lower()
        if ans in ['y', 'yes']:
            round_2 = True
            break
        elif ans in ['n', 'no']:
            round_2 = False
            break
        print(f"  {RED}✖ พิมพ์ผิด! กรุณาตอบเฉพาะ 'y' หรือ 'n' เท่านั้น{RESET}")

    # 3. ถาม Boost
    while True:
        ans = input(f"{YELLOW}▶ กด Boost ไหม? {BOLD}(y/n):{RESET} ").strip().lower()
        if ans in ['y', 'yes']:
            boost_mode = True
            break
        elif ans in ['n', 'no']:
            boost_mode = False
            break
        print(f"  {RED}✖ พิมพ์ผิด! กรุณาตอบเฉพาะ 'y' หรือ 'n' เท่านั้น{RESET}")

    # 3.1 เลือก Boost 1-11 (ถ้าเลือก Boost)
    selected_num = None
    selected_boost = None

    if boost_mode:
        boost_options = [
            "Double_Coins",             # [1]
            "15%_score_bonus",          # [2]
            "-15%_HP_drain",            # [3]
            "Revive_once_with_80_HP",   # [4]
            "70%_Crush_Chance",         # [5]
            "+17%_base_speed",          # [6]
            "Gold_Coin_Magic",          # [7]
            "-30%_collision_damage",    # [8]
            "+20%_HP_from_potions",     # [9]
            "Magnetic_Aura",            # [10]
            "2_Pit_Lifts"               # [11]
        ]

        print(f"\n{BLUE}┌──────────────────────────────────────────────────────────┐")
        print(f"│ {BOLD}{MAGENTA}⚡ Pick desired Boosts! (เลือกหมายเลข 1 - 11){RESET}{BLUE}             │")
        print(f"├──────────────────────────────────────────────────────────┤")
        for idx, opt in enumerate(boost_options, 1):
            item_str = f"{opt} [{idx}]"
            print(f"│  {GREEN}{item_str:<54}{BLUE}│")
        print(f"└──────────────────────────────────────────────────────────┘{RESET}")

        while True:
            user_input = input(f"\n{YELLOW}▶ กรุณาใส่หมายเลข Boost ที่ต้องการ (1-11):{RESET} ").strip()
            if not user_input.isdigit():
                print(f"  {RED}✖ พิมพ์ผิด! กรุณากรอกเฉพาะตัวเลขเท่านั้น (เช่น 1, 2, 3){RESET}")
                continue
            
            choice = int(user_input)
            if 1 <= choice <= 11:
                selected_num = choice
                selected_boost = boost_options[choice - 1]
                break
            else:
                print(f"  {RED}✖ พิมพ์ผิด! หมายเลขต้องอยู่ระหว่าง 1 ถึง 11 เท่านั้น{RESET}")

    # Return ผลลัพธ์กลับออกไปเป็น Dictionary
    return {
        "fast_start": fast_start,
        "round_2": round_2,
        "boost_mode": boost_mode,
        "boost_id": selected_num,
        "boost_name": selected_boost
    }


# ==========================================
# ตัวอย่างการเรียกใช้งานฟังก์ชัน
# ==========================================
if __name__ == "__main__":
    # เรียกใช้ฟังก์ชันแล้วรับค่าใส่ตัวแปร result
    result = get_user_configuration()

    # ลอง print ค่าที่ return กลับมาดู
    print("\n--- RETURN VALUE ---")
    print(result)