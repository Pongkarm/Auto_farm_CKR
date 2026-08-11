def get_user_configuration(config=None):
    import json
    
    # 🟢 ถ้าไม่มี config ส่งมา ให้พยายามอ่านจากไฟล์ Config.json
    if config is None:
        try:
            with open("Config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            config = {}

    # ANSI Color Codes
    RESET, BOLD = "\033[0m", "\033[1m"
    CYAN, GREEN, YELLOW = "\033[96m", "\033[92m", "\033[93m"
    MAGENTA, RED, BLUE = "\033[95m", "\033[91m", "\033[94m"

    # Header
    print(f"\n{CYAN}═" * 58)
    print(f"{BOLD}{MAGENTA}  ✨ GAME SETUP CONFIGURATION ✨".center(66))
    print(f"{CYAN}═" * 58 + f"{RESET}\n")

    boost_options = [
        "No_Boost",                 # [0]
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

    # 🟢 เช็คว่าเปิดใช้งาน Auto Setup จาก Config หรือไม่
    if config.get("auto_setup", False):
        print(f"{GREEN}⚙️ [Auto Setup] กำลังเปิดใช้งานการตั้งค่าอัตโนมัติจาก Config.json...{RESET}")
        fast_start = config.get("fast_start", False)
        round_2 = config.get("round_2", False)
        boost_name = config.get("boost_name", "Double_Coins")
        
        # 🟢 ตรวจสอบสถานะ boost_mode จาก boost_name (ถ้าเป็น "0", 0, None หรือว่าง ถือว่าไม่ใช้)
        boost_mode = boost_name not in ["0", 0, None, "", "None"]
        boost_id = None
        if boost_mode and boost_name in boost_options:
            boost_id = boost_options.index(boost_name) + 1
            
        print(f"  - Fast Start: {GREEN}{fast_start}{RESET}")
        print(f"  - ผลัด 2: {GREEN}{round_2}{RESET}")
        print(f"  - Boost Name: {CYAN}{boost_name if boost_mode else 'ไม่ใช้ (0)'}{RESET}")
        print(f"{CYAN}═" * 58 + f"{RESET}\n")
        
        return {
            "fast_start": fast_start,
            "round_2": round_2,
            "boost_mode": boost_mode,
            "boost_id": boost_id,
            "boost_name": boost_name if boost_mode else "0"
        }

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

    # 3. เลือก Boost (ใส่ 0 คือไม่ใช้ Boost)
    print(f"\n{BLUE}┌──────────────────────────────────────────────────────────┐")
    print(f"│ {BOLD}{MAGENTA}⚡ Pick desired Boosts! (เลือกหมายเลข 0 - 11){RESET}{BLUE}             │")
    print(f"├──────────────────────────────────────────────────────────┤")
    print(f"│  {RED}ไม่ใช้ Boost [0]{RESET}{BLUE}                                         │")
    for idx, opt in enumerate(boost_options, 1):
        item_str = f"{opt} [{idx}]"
        print(f"│  {GREEN}{item_str:<54}{BLUE}│")
    print(f"└──────────────────────────────────────────────────────────┘{RESET}")

    selected_num = None
    selected_boost = "0"
    boost_mode = False

    while True:
        user_input = input(f"\n{YELLOW}▶ กรุณาใส่หมายเลข Boost ที่ต้องการ (0-11):{RESET} ").strip()
        if not user_input.isdigit():
            print(f"  {RED}✖ พิมพ์ผิด! กรุณากรอกเฉพาะตัวเลขเท่านั้น (เช่น 0, 1, 2){RESET}")
            continue
        
        choice = int(user_input)
        if choice == 0:
            boost_mode = False
            selected_boost = "0"
            selected_num = None
            break
        elif 1 <= choice <= 11:
            boost_mode = True
            selected_num = choice
            selected_boost = boost_options[choice - 1]
            break
        else:
            print(f"  {RED}✖ พิมพ์ผิด! หมายเลขต้องอยู่ระหว่าง 0 ถึง 11 เท่านั้น{RESET}")

    return {
        "fast_start": fast_start,
        "round_2": round_2,
        "boost_mode": boost_mode,
        "boost_id": selected_num,
        "boost_name": selected_boost
    }

if __name__ == "__main__":
    result = get_user_configuration()
    print("\n--- RETURN VALUE ---")
    print(result)