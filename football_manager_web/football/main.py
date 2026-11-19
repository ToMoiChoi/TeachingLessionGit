# -*- coding: utf-8 -*-
"""
Project: Football Manager Game
Mô tả: Game quản lý bóng đá, mô phỏng từ Hạng 2 lên Champions League.
Phiên bản: 1.0
Tác giả: [Tên bạn]
Ngày: 2025-03-01

Kiến trúc 6 module:
1. models.py       - Định nghĩa dữ liệu
2. game_engine.py  - Mô phỏng trận đấu
3. team_manager.py - Quản lý đội hình
4. league_manager.py - Quản lý giải đấu
5. save_load.py    - Lưu/tải game
6. ui.py           - Giao diện console

Hướng dẫn chạy: python main.py
"""
# ---------- Lớp giải đấu ----------
import random
from models import Player, Team, Match, League, POSITIONS, FIRST_NAMES, LAST_NAMES
from game_engine import simulate_match
from team_manager import is_valid_formation, substitute
from league_manager import update_standings
from save_load import save_game, load_game
from ui import *

# ---------- Hàm khởi tạo dữ liệu mẫu ----------
def create_random_players(count=16) -> list:
    """Tạo danh sách cầu thủ ngẫu nhiên."""
    players = []
    for _ in range(count):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        name = f"{first} {last}"
        pos = random.choice(POSITIONS)
        # Chỉ số ngẫu nhiên theo phân phối
        # 60%: 50-70, 30%: 70-85, 10%: 85-95
        r = random.random()
        if r < 0.6:
            att = random.randint(50, 70)
            deff = random.randint(50, 70)
            spd = random.randint(50, 70)
        elif r < 0.9:
            att = random.randint(70, 85)
            deff = random.randint(70, 85)
            spd = random.randint(70, 85)
        else:
            att = random.randint(85, 95)
            deff = random.randint(85, 95)
            spd = random.randint(85, 95)
        player = Player(name, pos, att, deff, spd)
        players.append(player)
    return players

def create_new_club():
    """Quy trình tạo CLB mới (4 bước)."""
    clear_screen()
    print_header("TẠO CLB MỚI")

    # Bước 1: Nhập tên
    name = get_input("Nhập tên CLB (tối thiểu 2 ký tự): ")
    while len(name) < 2:
        print("Tên quá ngắn!")
        name = get_input("Nhập lại tên CLB: ")

    # Bước 2: Chọn giải đấu (mặc định Hạng 2)
    league_name = "Hang 2"  # Có thể mở rộng chọn giải

    # Bước 3: Chọn sơ đồ
    formation = get_input("Chọn sơ đồ (4-3-3, 4-2-3-1, 5-3-2): ", "4-3-3")
    while formation not in ["4-3-3", "4-2-3-1", "5-3-2"]:
        print("Sơ đồ không hợp lệ!")
        formation = get_input("Chọn sơ đồ: ")

    # Bước 4: Xác nhận tạo
    print(f"\nCLB: {name}")
    print(f"Giải: {league_name}")
    print(f"Sơ đồ: {formation}")
    confirm = get_input("Xác nhận tạo CLB? (y/n): ")
    if confirm.lower() != 'y':
        print("Hủy tạo CLB.")
        return None

    # Sinh 16 cầu thủ
    players = create_random_players(16)
    team = Team(name, players)
    team.formation = formation

    # Lưu vào đối tượng Club (mở rộng)
    club = {
        "team": team,
        "league_name": league_name,
        "money": 5000000,
        "season": 1,
        "matches_played": 0,
        "points": 0,
        "position": 0,
        "passcode": None
    }
    print("\n✅ Tạo CLB thành công!")
    input("Nhấn Enter để tiếp tục...")
    return club

def main_menu():
    """Màn hình chính."""
    while True:
        clear_screen()
        print_header("FOOTBALL MANAGER")
        print_menu({
            "1": "Tạo CLB mới",
            "2": "Backup CLB (nạp game)",
            "3": "Thoát"
        })
        choice = get_input("Chọn: ")
        if choice == "1":
            club = create_new_club()
            if club:
                # Chuyển vào dashboard
                dashboard(club)
        elif choice == "2":
            load_club()
        elif choice == "3":
            print("Tạm biệt!")
            break
        else:
            print("Lựa chọn không hợp lệ!")

def dashboard(club):
    """Màn hình quản lý CLB sau khi tạo hoặc load."""
    while True:
        clear_screen()
        team = club["team"]
        print_header(f"DASHBOARD - {team.name}")
        print(f"Giải: {club['league_name']}  |  Mùa: {club['season']}")
        print(f"Tiền: ${club['money']:,}  |  Điểm: {club['points']}  |  Vị trí: {club['position']}")
        print_menu({
            "1": "Quản lý đội hình (Squad)",
            "2": "Xem lịch thi đấu",
            "3": "Bảng xếp hạng",
            "4": "About Salary",
            "5": "Chiến thuật",
            "6": "Thi đấu trận tiếp theo",
            "7": "Lưu game",
            "8": "Quay lại màn hình chính"
        })
        choice = get_input("Chọn: ")
        if choice == "1":
            show_players_list(team.players, "Danh sách cầu thủ")
            input("Nhấn Enter để quay lại...")
        elif choice == "2":
            # Tạm thời chưa implement
            print("Chức năng đang phát triển...")
            input("Nhấn Enter...")
        elif choice == "3":
            # Xem bảng xếp hạng
            print("Chức năng đang phát triển...")
            input("Nhấn Enter...")
        elif choice == "4":
            # About Salary
            total = team.total_salary()
            print(f"Tổng lương mùa này: ${total:,.2f}")
            avg = total / len(team.players) if team.players else 0
            print(f"Lương trung bình: ${avg:,.2f}")
            input("Nhấn Enter...")
        elif choice == "5":
            # Chiến thuật
            formation = get_input("Nhập sơ đồ mới (4-3-3, 4-2-3-1, 5-3-2): ", team.formation)
            if formation in ["4-3-3", "4-2-3-1", "5-3-2"]:
                team.formation = formation
                print(f"Đã đổi sơ đồ sang {formation}")
            else:
                print("Sơ đồ không hợp lệ!")
            input("Nhấn Enter...")
        elif choice == "6":
            # Thi đấu trận tiếp theo
            # Ở đây giả định có 1 đối thủ ngẫu nhiên
            opponent = Team("Đối thủ", create_random_players(16))
            match = Match(team, opponent, 1)
            # Chọn chiến thuật
            tactic = get_input("Chọn chiến thuật (Tan cong, Can bang, Phong thu): ", "Can bang")
            if tactic not in ["Tan cong", "Can bang", "Phong thu"]:
                tactic = "Can bang"
            # Mô phỏng
            print("Đang mô phỏng trận đấu...")
            match = simulate_match(match, tactic, "Can bang")  # đối thủ mặc định
            show_match_result(match)
            # Cập nhật điểm, tiền, v.v.
            club["points"] += match.points()
            club["matches_played"] += 1
            # Lưu tự động
            # (Tạm thời chưa lưu vì chưa có passcode)
            if club.get("passcode"):
                save_game(club, club["passcode"])
        elif choice == "7":
            # Lưu game
            if not club.get("passcode"):
                passcode = get_input("Tạo passcode để lưu game: ")
                club["passcode"] = passcode
            else:
                passcode = club["passcode"]
            # Chuẩn bị dữ liệu
            data = {
                "club_name": team.name,
                "league": club["league_name"],
                "season": club["season"],
                "money": club["money"],
                "players": [p.to_dict() for p in team.players],
                "formation": team.formation,
                "tactic": team.tactic,
                "matches_played": club["matches_played"],
                "points": club["points"],
                "position": club["position"]
            }
            save_game(data, passcode)
            print("💾 Lưu thành công!")
            input("Nhấn Enter...")
        elif choice == "8":
            break
        else:
            print("Lựa chọn không hợp lệ!")

def load_club():
    """Nạp game từ passcode."""
    passcode = get_input("Nhập passcode: ")
    data = load_game(passcode)
    if data:
        print("✅ Nạp game thành công!")
        # Tái tạo đối tượng Team từ dữ liệu
        team = Team(data["club_name"])
        team.players = [Player.from_dict(p) for p in data["players"]]
        team.formation = data.get("formation", "4-3-3")
        team.tactic = data.get("tactic", "Can bang")
        club = {
            "team": team,
            "league_name": data["league"],
            "season": data["season"],
            "money": data["money"],
            "matches_played": data["matches_played"],
            "points": data["points"],
            "position": data["position"],
            "passcode": passcode
        }
        dashboard(club)
    else:
        print("❌ Sai passcode hoặc không tìm thấy file lưu!")
        input("Nhấn Enter để tiếp tục...")

# ---------- Chạy chương trình ----------
if __name__ == "__main__":
    main_menu()