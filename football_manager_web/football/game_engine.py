# -*- coding: utf-8 -*-
import random

# ==============================================================================
# HỆ SỐ ĐÓNG GÓP THEO ĐẶC THÙ VỊ TRÍ (POSITION-SPECIFIC WEIGHTS)
# ==============================================================================
POSITION_WEIGHTS = {
    "GK":  {"att": 0.02, "def": 0.88, "spd": 0.10, "stamina_rate": 0.30},
    "CB":  {"att": 0.08, "def": 0.72, "spd": 0.20, "stamina_rate": 0.85},
    "LB":  {"att": 0.20, "def": 0.45, "spd": 0.35, "stamina_rate": 1.00},
    "RB":  {"att": 0.20, "def": 0.45, "spd": 0.35, "stamina_rate": 1.00},
    "LWB": {"att": 0.30, "def": 0.35, "spd": 0.35, "stamina_rate": 1.25},
    "RWB": {"att": 0.30, "def": 0.35, "spd": 0.35, "stamina_rate": 1.25},
    "CDM": {"att": 0.18, "def": 0.58, "spd": 0.24, "stamina_rate": 1.10},
    "CM":  {"att": 0.35, "def": 0.35, "spd": 0.30, "stamina_rate": 1.10},
    "CAM": {"att": 0.60, "def": 0.15, "spd": 0.25, "stamina_rate": 1.00},
    "LM":  {"att": 0.40, "def": 0.25, "spd": 0.35, "stamina_rate": 1.05},
    "RM":  {"att": 0.40, "def": 0.25, "spd": 0.35, "stamina_rate": 1.05},
    "LW":  {"att": 0.52, "def": 0.10, "spd": 0.38, "stamina_rate": 1.00},
    "RW":  {"att": 0.52, "def": 0.10, "spd": 0.38, "stamina_rate": 1.00},
    "ST":  {"att": 0.72, "def": 0.05, "spd": 0.23, "stamina_rate": 1.00},
    "CF":  {"att": 0.65, "def": 0.10, "spd": 0.25, "stamina_rate": 1.00},
}

DEFAULT_WEIGHT = {"att": 0.33, "def": 0.33, "spd": 0.34, "stamina_rate": 1.00}


def calculate_team_strength(team, tactic="Can bang"):
    """
    Tính toán chỉ số sức mạnh của đội hình dựa trên:
    - Trọng số chuyên biệt của từng vị trí (GK, CB, CDM, CAM, ST...)
    - Hiệu ứng mỏ neo CDM (lá chắn trước vòng 16m50)
    - Hiệu ứng tiền vệ kiểm soát trung tuyến (CM, CAM, CDM)
    - Tác động của thẻ đỏ (thiếu quân số)
    - Chiến thuật thi đấu (Tấn công / Phòng thủ / Cân bằng)
    """
    starting_players = team.get_starting_xi()
    if not starting_players:
        return {"attack": 50, "defense": 50, "speed": 50, "overall": 50, "active_count": 0, "midfield": 50}

    # Lọc bỏ cầu thủ đã nhận thẻ đỏ
    active_players = [p for p in starting_players if getattr(p, 'red_cards', 0) == 0]
    if not active_players:
        active_players = starting_players

    manpower_ratio = min(1.0, len(active_players) / 11.0)

    # 1. Tính toán đóng góp theo trọng số vị trí
    eff_att_sum = 0.0
    eff_def_sum = 0.0
    eff_spd_sum = 0.0
    midfield_power = 0.0
    has_cdm = False

    for p in active_players:
        pos = getattr(p, 'position', 'CM')
        w = POSITION_WEIGHTS.get(pos, DEFAULT_WEIGHT)
        stam = max(0.2, p.stamina / 100.0)

        # Đóng góp tấn công: Tiền đạo và Tiền vệ công nhân hệ số cao
        p_att = (p.attack * 0.75 + p.speed * 0.25) * w["att"] * 3.0 * stam
        # Đóng góp phòng ngự: Hậu vệ và Thủ môn, Tiền vệ phòng ngự nhân hệ số cao
        p_def = (p.defense * 0.75 + p.speed * 0.25) * w["def"] * 3.0 * stam
        # Đóng góp tốc độ
        p_spd = p.speed * w["spd"] * 3.0 * stam

        eff_att_sum += p_att
        eff_def_sum += p_def
        eff_spd_sum += p_spd

        if pos in ['CDM', 'CM', 'CAM', 'LM', 'RM']:
            midfield_power += (p.attack * 0.4 + p.defense * 0.4 + p.speed * 0.2) * stam
        if pos == 'CDM':
            has_cdm = True

    count = len(active_players)
    total_att = (eff_att_sum / count) * manpower_ratio
    total_def = (eff_def_sum / count) * manpower_ratio
    total_spd = (eff_spd_sum / count) * manpower_ratio

    # 2. Hiệu ứng lá chắn mỏ neo (CDM Shield Effect)
    if has_cdm:
        total_def *= 1.06

    # 3. Điều chỉnh theo chiến thuật
    if tactic == "Tan cong":
        total_att *= 1.16
        total_def *= 0.90
    elif tactic in ["Phong thu", "Xe bus"]:
        total_att *= 0.80
        total_def *= 1.28
    elif tactic == "Tiki-Taka":
        midfield_power *= 1.22
        total_att *= 1.08
        total_def *= 1.06
    elif tactic == "Phan cong":
        total_spd *= 1.20
        total_att *= 1.14
        total_def *= 1.10

    overall = (total_att * 0.4 + total_def * 0.4 + total_spd * 0.2)
    return {
        "attack": total_att,
        "defense": total_def,
        "speed": total_spd,
        "overall": overall,
        "active_count": len(active_players),
        "midfield": midfield_power
    }


def get_position_shot_profile(player):
    """
    Xác định hồ sơ dứt điểm:
    1. Cự ly dứt điểm tuân theo chuẩn yêu cầu:
       - 75%: Trong vòng cấm (< 16.5m, từ 5.5m - 16.0m)
       - 20%: Rìa vòng cấm 16m50 - 20m (từ 16.5m - 20.0m)
       - 5%: Sút xa > 20m trên phần sân đối thủ (từ 21.0m - 34.0m)
    2. Hành vi, mô tả động tác sút và tỷ lệ ăn bàn phản ánh chân thực vị trí của cầu thủ.
    """
    pos = getattr(player, 'position', 'ST')
    dist_roll = random.random()

    if dist_roll < 0.75:
        # 75% TRONG VÒNG CẤM (< 16.5m)
        dist = round(random.uniform(5.5, 16.0), 1)
        shot_zone = "in_box"
        if pos in ['ST', 'CF']:
            base_prob = 0.45
            desc = random.choice([
                f"đè mặt trung vệ xoay người vô-lê một chạm hiểm hóc ở cự ly {dist}m trong vòng cấm",
                f"băng cắt dũng mãnh đệm bóng cận thành một chạm ở cự ly {dist}m trong vòng 16m50",
                f"bật cao vượt qua trung vệ đánh đầu lái bóng vào góc xa cự ly {dist}m trong vòng cấm địa",
                f"chớp thời cơ đối mặt thủ môn dứt điểm chìm hiểm hóc ở cự ly {dist}m trong vòng cấm",
                f"thoát bẫy việt vị đệm bóng cận thành một chạm ở cự ly {dist}m"
            ])
        elif pos in ['LW', 'RW']:
            base_prob = 0.40
            desc = random.choice([
                f"bó thẳng từ đáy biên vào vòng cấm dứt điểm chéo góc hiểm hóc ở cự ly {dist}m",
                f"xâm nhập nách trung lộ đón đường chuyền đệm bóng một chạm ở cự ly {dist}m trong vòng cấm",
                f"đảo chân vượt qua hậu vệ biên rồi sút căng vào góc gần ở cự ly {dist}m trong vòng 16m50"
            ])
        elif pos in ['CAM']:
            base_prob = 0.38
            desc = random.choice([
                f"bất ngờ xâm nhập vòng cấm đón đường chọc khe dứt điểm tinh tế ở cự ly {dist}m",
                f"phối hợp bật nhả tam giác trung lộ rồi dứt điểm chìm ở cự ly {dist}m trong vòng 16m50"
            ])
        elif pos in ['CM', 'CDM', 'LM', 'RM']:
            base_prob = 0.34
            desc = f"băng lên dũng mãnh từ tuyến hai đệm bóng một chạm ở cự ly {dist}m trong vòng cấm"
        else: # Hậu vệ
            base_prob = 0.32
            desc = random.choice([
                f"lên tham gia quả phạt góc bật cao đánh đầu hiểm hóc ở cự ly {dist}m trong vòng cấm",
                f"dâng cao hỗ trợ tấn công chớp thời cơ đệm bóng cận thành cự ly {dist}m"
            ])

    elif dist_roll < 0.95:
        # 20% RÌA VÒNG CẤM 16M50 - 20M
        dist = round(random.uniform(16.5, 20.0), 1)
        shot_zone = "edge_box"
        if pos in ['CAM']:
            base_prob = 0.26
            desc = random.choice([
                f"đón đường nhả bóng tuyến hai vung chân nã đại bác xé gió găm thẳng vào góc cao ở cự ly {dist}m",
                f"cứa lòng kỹ thuật điệu nghệ vẽ đường cong ma thuật từ cự ly {dist}m rìa vòng 16m50",
                f"chớp thời cơ dứt điểm mu lai má hiểm hóc từ khoảng cách {dist}m sát vòng cấm"
            ])
        elif pos in ['LW', 'RW']:
            base_prob = 0.24
            desc = random.choice([
                f"bó vào nách trung lộ cứa lòng chân nghịch hình quả chuối găm vào góc chữ A từ cự ly {dist}m",
                f"nhấp bóng vượt qua hậu vệ biên rồi vung chân nã đại bác sát rìa vòng 16m50 ở cự ly {dist}m",
                f"cứa lòng má trong kỹ thuật đưa bóng lượn qua tầm với thủ môn từ cự ly {dist}m ngoài vòng cấm"
            ])
        elif pos in ['ST', 'CF']:
            base_prob = 0.24
            desc = random.choice([
                f"xoay người tung cú sút mu chính diện hiểm hóc từ cự ly {dist}m rìa vòng cấm 16m50",
                f"bắt vô-lê chớp nhoáng bóng hai sát mép vòng cấm ở cự ly {dist}m",
                f"nhấp một nhịp loại bỏ hậu vệ rồi sút căng chìm ở cự ly {dist}m rìa vòng cấm"
            ])
        elif pos in ['CM', 'CDM', 'LM', 'RM']:
            base_prob = 0.20
            desc = random.choice([
                f"bắt vô-lê sấm sét khi bóng bật ra từ tuyến hai ở cự ly {dist}m rìa vòng cấm 16m50",
                f"băng lên tiếp ứng vung mu chính diện đưa bóng găm sát cột dọc từ cự ly {dist}m"
            ])
        else: # Hậu vệ
            base_prob = 0.16
            desc = f"đón bóng phá ra từ tuyến hai tung cú sút xa trái phá ở cự ly {dist}m rìa vòng cấm"

    else:
        # 5% SÚT XA TỪ CỰ LY > 20M TRÊN PHẦN SÂN ĐỐI THỦ
        dist = round(random.uniform(21.0, 33.0), 1)
        shot_zone = "long_range"
        if pos in ['CAM']:
            base_prob = 0.12
            desc = f"quan sát thấy thủ môn dâng cao, nã rocket siêu phẩm muôn phần uy lực từ khoảng cách xa {dist}m"
        elif pos in ['CM', 'CDM']:
            base_prob = 0.09
            desc = f"vung chân nã đại bác sấm sét từ cự ly rất xa {dist}m bên phần sân đối phương khiến thủ môn vất vả"
        elif pos in ['LW', 'RW']:
            base_prob = 0.08
            desc = f"táo bạo nã đại bác cầu âu từ góc chếch ngoài biên cự ly {dist}m bên phần sân đối thủ"
        elif pos in ['ST', 'CF']:
            base_prob = 0.09
            desc = f"bất ngờ vung chân nã rocket sấm sét từ cự ly xa {dist}m bên phần sân đối phương"
        else: # Hậu vệ
            base_prob = 0.06
            desc = f"dâng cao táo bạo tung cú sút xa cầu may từ cự ly {dist}m"

    return dist, desc, shot_zone, base_prob


def get_position_assist_desc(passer):
    """Mô tả đường kiến tạo mang phong cách chiến thuật của vị trí kiến tạo."""
    pos = getattr(passer, 'position', 'CM')
    if pos in ['CAM', 'CM']:
        return random.choice([
            f"đường chọc khe xé toang hàng phòng ngự của [{pos}] {passer.name}",
            f"pha tỉa bóng nhãn quan siêu đẳng từ [{pos}] {passer.name}",
            f"cú bấm bóng điểm rơi tinh tế của [{pos}] {passer.name}"
        ])
    elif pos in ['LW', 'RW']:
        return random.choice([
            f"pha dốc bóng sát đáy biên rồi căng ngang dọn cỗ của [{pos}] {passer.name}",
            f"quả tạt bóng loại bỏ hoàn toàn thủ môn của [{pos}] {passer.name}"
        ])
    elif pos in ['LB', 'RB', 'LWB', 'RWB']:
        return random.choice([
            f"pha chồng biên tốc độ rồi tạt bóng chuẩn xác của [{pos}] {passer.name}",
            f"đường chuyền vượt tuyến chuẩn từng milimet của [{pos}] {passer.name}"
        ])
    elif pos in ['ST', 'CF']:
        return f"pha làm tường nhả bóng vừa tầm của [{pos}] {passer.name}"
    else:
        return f"đường chuyền tiếp ứng của [{pos}] {passer.name}"


def run_minutes(match, start_min, end_min, home_tactic="Can bang", away_tactic="Can bang"):
    """
    Mô phỏng trận đấu theo từng phút tích hợp sâu cơ chế nhiệm vụ các vị trí:
    - Tiêu hao thể lực theo đặc thù vị trí (LWB/RWB hao nhiều nhất, GK hao ít nhất)
    - Tỷ lệ sút và cự ly dứt điểm phản ánh đúng vai trò (ST 82% trong vòng cấm, CAM sút xa 16m50-20m)
    - Rê bóng 1-on-1 theo cặp vị trí tương ứng (LW vs RB, CAM vs CDM, ST vs CB)
    - Phạm lỗi, Thẻ phạt và Phạt đền 11m phản ánh đúng khu vực nhiệm vụ
    """
    home_team = match.home_team
    away_team = match.away_team

    for minute in range(start_min, end_min + 1):
        # 1. Danh sách cầu thủ còn thi đấu trên sân
        home_active = [p for p in home_team.get_starting_xi() if getattr(p, 'red_cards', 0) == 0]
        away_active = [p for p in away_team.get_starting_xi() if getattr(p, 'red_cards', 0) == 0]

        if not home_active or not away_active:
            continue

        # Thông báo bù giờ hiệp 1 & hiệp 2 từ bảng điện tử trọng tài bàn
        if minute == 45:
            extra_min = random.choice([2, 3, 4])
            match.add_event(
                45,
                f"⏱️ BẢNG BÙ GIỜ! Trọng tài bàn giơ bảng LED: Hiệp 1 có +{extra_min} phút bù giờ!",
                event_type="injury_time",
                data={"half": 1, "extra_minutes": extra_min}
            )
        elif minute == 90:
            extra_min = random.choice([3, 4, 5])
            match.add_event(
                90,
                f"⏱️ BẢNG BÙ GIỜ! Trọng tài bàn giơ bảng LED: Hiệp 2 có +{extra_min} phút bù giờ!",
                event_type="injury_time",
                data={"half": 2, "extra_minutes": extra_min}
            )

        # 2. Tiêu hao thể lực theo đặc thù vị trí
        base_loss = 0.35 if home_tactic == "Tan cong" else (0.22 if home_tactic in ["Phong thu", "Xe bus"] else (0.32 if home_tactic == "Phan cong" else 0.28))
        for p in home_active:
            w = POSITION_WEIGHTS.get(getattr(p, 'position', 'CM'), DEFAULT_WEIGHT)
            loss = base_loss * w.get("stamina_rate", 1.0)
            p.stamina = max(10.0, p.stamina - loss)

        for p in away_active:
            w = POSITION_WEIGHTS.get(getattr(p, 'position', 'CM'), DEFAULT_WEIGHT)
            loss = 0.28 * w.get("stamina_rate", 1.0)
            p.stamina = max(10.0, p.stamina - loss)

        # 3. Đánh giá sức mạnh hai đội ở phút hiện tại
        home_str = calculate_team_strength(home_team, home_tactic)
        away_str = calculate_team_strength(away_team, away_tactic)

        total_power = home_str["overall"] + away_str["overall"]
        home_prob = home_str["overall"] / total_power if total_power > 0 else 0.5

        # Tác động của cuộc chiến khu trung tuyến (Midfield Domination)
        mid_diff = (home_str.get("midfield", 50) - away_str.get("midfield", 50)) / max(1.0, home_str.get("midfield", 50) + away_str.get("midfield", 50))
        home_prob = min(0.85, max(0.15, home_prob + mid_diff * 0.12))

        # 4. Quyết định biến cố trong phút thi đấu
        roll = random.random()

        # ==========================================================
        # NHÁNH 1: TÌNH HUỐNG DỨT ĐIỂM (Xác suất ~23% mỗi phút)
        # ==========================================================
        if roll < 0.23:
            is_home_attack = (random.random() < home_prob)
            att_team = home_team if is_home_attack else away_team
            def_team = away_team if is_home_attack else home_team
            att_players = home_active if is_home_attack else away_active
            def_players = away_active if is_home_attack else home_active

            if not att_players or not def_players:
                continue

            # Cập nhật tổng số cú sút
            if is_home_attack:
                match.shots_home += 1
            else:
                match.shots_away += 1

            # Chọn cầu thủ dứt điểm theo trọng số vai trò vị trí
            def get_shot_weight(pos):
                if pos in ['ST', 'CF']: return 45
                if pos in ['LW', 'RW']: return 22
                if pos in ['CAM']: return 16
                if pos in ['CM', 'LM', 'RM']: return 10
                if pos == 'CDM': return 4
                return 3

            shot_weights = [get_shot_weight(getattr(p, 'position', 'CM')) for p in att_players]
            shooter = random.choices(att_players, weights=shot_weights, k=1)[0]

            # Chọn người kiến tạo (ưu tiên CAM, CM, Winger)
            passer_candidates = [p for p in att_players if p != shooter and getattr(p, 'position', '') != 'GK']
            passer = None
            if passer_candidates and random.random() < 0.72:
                def get_pass_weight(pos):
                    if pos in ['CAM', 'CM']: return 35
                    if pos in ['LW', 'RW', 'LM', 'RM']: return 25
                    if pos in ['LB', 'RB', 'LWB', 'RWB']: return 18
                    if pos in ['ST', 'CF']: return 12
                    return 5
                pass_weights = [get_pass_weight(getattr(p, 'position', 'CM')) for p in passer_candidates]
                passer = random.choices(passer_candidates, weights=pass_weights, k=1)[0]

            # Lấy hồ sơ cự ly sút đặc thù của vị trí
            dist, shot_desc, shot_type_label, base_prob = get_position_shot_profile(shooter)

            # Tương quan giữa Shooter và Thủ môn GK đối phương
            shooter_pos = getattr(shooter, 'position', 'ST')
            shooter_power = (shooter.attack * 0.75 + shooter.speed * 0.25) * (shooter.stamina / 100.0)

            # Thủ môn đối phương cản phá
            gk = next((p for p in def_players if getattr(p, 'position', '') == 'GK'), def_players[0])
            gk_power = (gk.defense * 0.85 + gk.speed * 0.15) * (gk.stamina / 100.0)

            # Nếu đối phương có CDM bọc lót trước vòng cấm
            has_opp_cdm = any(getattr(p, 'position', '') == 'CDM' for p in def_players)
            if has_opp_cdm and shot_type_label in ["in_box", "edge_box"]:
                base_prob *= 0.92

            ratio = shooter_power / max(1.0, gk_power)
            final_prob = min(0.88, base_prob * ratio)

            shooter_tag = f"[{shooter_pos}] {shooter.name}"

            if random.random() < final_prob:
                # 8% cơ hội kích hoạt VAR kiểm tra việt vị khi ghi bàn
                if random.random() < 0.08:
                    is_offside_disallowed = (random.random() < 0.35)
                    if is_offside_disallowed:
                        match.add_event(
                            minute,
                            f"🖥️ VAR TỪ CHỐI BÀN THẮNG! Phút {minute}: Trọng tài tham khảo VAR và xác định {shooter_tag} đã việt vị li ti khi nhận bóng! Bàn thắng không được công nhận!",
                            event_type="var_check",
                            data={"is_home": is_home_attack, "check_type": "offside", "decision": "disallowed", "player": shooter.name}
                        )
                        continue
                    else:
                        match.add_event(
                            minute,
                            f"🖥️ VAR XÁC NHẬN! Phút {minute}: Phòng VAR kiểm tra kĩ lưỡng đường chuyền và xác định {shooter_tag} không hề việt vị! Bàn thắng hợp lệ!",
                            event_type="var_check",
                            data={"is_home": is_home_attack, "check_type": "offside", "decision": "confirmed", "player": shooter.name}
                        )

                # BÀN THẮNG (GOAL)
                if is_home_attack:
                    match.home_goals += 1
                    match.target_home += 1
                else:
                    match.away_goals += 1
                    match.target_away += 1

                shooter.goals += 1
                assist_text = f" (kiến tạo: {get_position_assist_desc(passer)})" if passer else ""
                match.add_event(
                    minute,
                    f"⚽ VÀOOO! Phút {minute}: {shooter_tag} ({att_team.name}) {shot_desc}{assist_text}! Tỉ số: {match.home_goals}-{match.away_goals}",
                    event_type="goal",
                    data={"is_home": is_home_attack, "dist": dist, "shooter": shooter.name, "zone": shot_type_label, "pos": shooter_pos}
                )
            else:
                # KHÔNG VÀO
                is_target = (random.random() < 0.60)
                is_woodwork = (random.random() < 0.22 and dist <= 28)
                woodwork_type = random.choice(['crossbar', 'post']) if is_woodwork else None

                if is_target or is_woodwork:
                    if is_home_attack:
                        match.target_home += 1
                    else:
                        match.target_away += 1

                gk_tag = f"[GK] {gk.name}"
                if is_woodwork:
                    if woodwork_type == 'crossbar':
                        res_desc = "nhưng bóng đập trúng XÀ NGANG rung chuyển khung gỗ bật ra ngoài đầy tiếc nuối!"
                    else:
                        res_desc = "nhưng bóng liếm mép CỘT DỌC dội ngược lại mặt cỏ sân thi đấu!"
                else:
                    reasons = [
                        f"nhưng thủ môn {gk_tag} đã xuất sắc bay người cản phá ngoạn mục",
                        f"nhưng bóng đi chệch cột dọc trong gang tấc",
                        f"nhưng trung vệ đối phương đã kịp thời lăn xả xoạc bóng giải nguy trên vạch vôi"
                    ]
                    res_desc = random.choice(reasons)

                match.add_event(
                    minute,
                    f"🧤 Cơ hội! Phút {minute}: {shooter_tag} ({att_team.name}) {shot_desc}, {res_desc}",
                    event_type="shot_miss",
                    data={
                        "is_home": is_home_attack,
                        "dist": dist,
                        "shooter": shooter.name,
                        "target": is_target,
                        "pos": shooter_pos,
                        "woodwork": woodwork_type
                    }
                )

        # ==========================================================
        # NHÁNH 2: RÊ BÓNG & ĐỐI ĐẦU 1-ON-1 THEO CẶP VỊ TRÍ (~18% mỗi phút)
        # ==========================================================
        elif roll < 0.41:
            is_home_dribble = (random.random() < home_prob)
            att_team = home_team if is_home_dribble else away_team
            def_team = away_team if is_home_dribble else home_team
            att_players = home_active if is_home_dribble else away_active
            def_players = away_active if is_home_dribble else home_active

            if not att_players or not def_players:
                continue

            # Chọn Dribbler ưu tiên hàng cánh & hộ công
            dribbler_candidates = [p for p in att_players if getattr(p, 'position', '') in ['LW', 'RW', 'CAM', 'ST', 'LWB', 'RWB', 'LM', 'RM']]
            dribbler = random.choice(dribbler_candidates) if dribbler_candidates else random.choice(att_players)
            dribbler_pos = getattr(dribbler, 'position', 'ST')

            # Ghép cặp Hậu vệ đối mặt theo vị trí chiến thuật thực tế
            if dribbler_pos == 'LW':
                matched_defs = [p for p in def_players if getattr(p, 'position', '') in ['RB', 'RWB', 'CB']]
            elif dribbler_pos == 'RW':
                matched_defs = [p for p in def_players if getattr(p, 'position', '') in ['LB', 'LWB', 'CB']]
            elif dribbler_pos in ['CAM', 'ST', 'CF']:
                matched_defs = [p for p in def_players if getattr(p, 'position', '') in ['CB', 'CDM']]
            elif dribbler_pos in ['LWB', 'LB']:
                matched_defs = [p for p in def_players if getattr(p, 'position', '') in ['RW', 'RM', 'RB']]
            elif dribbler_pos in ['RWB', 'RB']:
                matched_defs = [p for p in def_players if getattr(p, 'position', '') in ['LW', 'LM', 'LB']]
            else:
                matched_defs = [p for p in def_players if getattr(p, 'position', '') in ['CB', 'CDM', 'CM']]

            defender = random.choice(matched_defs) if matched_defs else random.choice(def_players)
            defender_pos = getattr(defender, 'position', 'CB')

            # Kỹ năng đặc thù gắn liền với vị trí & tên chiêu thức nổi bật
            if dribbler_pos in ['LW', 'RW']:
                skill_title, chosen_skill = random.choice([
                    ("STEP-OVER", "thực hiện pha đảo chân Step-over liên hồi xé gió dọc hành lang biên"),
                    ("ELASTICO", "thực hiện pha búng bóng Elastico cực nhanh đổi hướng chớp nhoáng bó vào trung lộ"),
                    ("RAINBOW FLICK", "gắp bóng qua đầu Rainbow Flick đậm chất Samba nghệ sĩ qua đầu hậu vệ"),
                    ("LA CROQUETA", "lướt bóng La Croqueta chuyển chân siêu dính đánh bại chốt chặn")
                ])
            elif dribbler_pos == 'CAM':
                skill_title, chosen_skill = random.choice([
                    ("ROULETTE", "dùng kỹ thuật xoay compa Marseille Roulette điệu nghệ thoát pressing"),
                    ("NUTMEG", "xâu kim xỏ háng Nutmeg ngẫu hứng qua hai chân tiền vệ phòng ngự đối phương"),
                    ("RABONA FAKE", "làm động tác giả sút Rabona Fake ngoặt bóng loại bỏ trung vệ")
                ])
            elif dribbler_pos in ['ST', 'CF']:
                skill_title, chosen_skill = random.choice([
                    ("BODY FEINT", "lắc hông làm động tác giả Body Feint đánh lừa trung vệ"),
                    ("CHOP TURN", "giật gót Ronaldo Chop đổi hướng đột ngột mở góc dứt điểm"),
                    ("POWER DRIBBLE", "dùng thể hình tì đè càn lướt xoay người qua mặt trung vệ đối phương đầy dũng mãnh")
                ])
            elif dribbler_pos in ['LWB', 'RWB', 'LB', 'RB']:
                skill_title, chosen_skill = ("SPEED BURST", "đẩy bóng dài bứt tốc thần sầu Speed Dribbler leo biên dũng mãnh")
            else:
                skill_title, chosen_skill = ("SKILL MOVE", "nhấp bóng kỹ thuật loại bỏ sự đeo bám của đối thủ")

            dribbler_score = (dribbler.speed * 0.6 + dribbler.attack * 0.4) * (dribbler.stamina / 100.0)
            defender_score = (defender.defense * 0.6 + defender.speed * 0.4) * (defender.stamina / 100.0)

            # Bonus cho hậu vệ chuyên trách (CB, CDM)
            if defender_pos in ['CB', 'CDM']:
                defender_score *= 1.08

            success_prob = min(0.85, max(0.25, 0.52 * (dribbler_score / max(1.0, defender_score))))

            dribbler_tag = f"[{dribbler_pos}] {dribbler.name}"
            defender_tag = f"[{defender_pos}] {defender.name}"

            if random.random() < success_prob:
                outcomes = [
                    f"mở ra góc dọn cỗ cực kỳ thoáng đãng cho đồng đội",
                    f"xâm nhập thẳng vào nách trung lộ đối phương",
                    f"loại bỏ hoàn toàn sự kèm cặp khiến khán đài trầm trồ"
                ]
                match.add_event(
                    minute,
                    f"🪄 Kỹ thuật! Phút {minute}: {dribbler_tag} ({att_team.name}) {chosen_skill} vượt qua {defender_tag}, {random.choice(outcomes)}!",
                    event_type="dribble_success",
                    data={
                        "is_home": is_home_dribble,
                        "dribbler": dribbler.name,
                        "defender": defender.name,
                        "skill_title": skill_title,
                        "dribbler_pos": dribbler_pos,
                        "defender_pos": defender_pos
                    }
                )
            else:
                tackle_acts = [
                    f"đã đọc bài chuẩn xác và xoạc bóng giải nguy kịp thời",
                    f"dùng thể hình tì đè đoạt lại quyền kiểm soát bóng chắc chắn",
                    f"áp sát quyết liệt bẻ gãy đợt đột phá biên",
                    f"bọc lót thông minh cắt bóng an toàn"
                ]
                match.add_event(
                    minute,
                    f"🛡️ Đánh chặn! Phút {minute}: {dribbler_tag} ({att_team.name}) nỗ lực {chosen_skill}, nhưng {defender_tag} ({def_team.name}) {random.choice(tackle_acts)}.",
                    event_type="dribble_tackle",
                    data={
                        "is_home": is_home_dribble,
                        "dribbler": dribbler.name,
                        "defender": defender.name,
                        "skill_title": skill_title,
                        "dribbler_pos": dribbler_pos,
                        "defender_pos": defender_pos
                    }
                )

        # ==========================================================
        # NHÁNH 3: PHẠM LỖI, THẺ PHẠT & PENALTY THEO KHU VỰC (~13% mỗi phút)
        # ==========================================================
        elif roll < 0.51:
            is_home_foul = (random.random() < 0.50)
            foul_team = home_team if is_home_foul else away_team
            victim_team = away_team if is_home_foul else home_team
            foul_players = home_active if is_home_foul else away_active
            victim_players = away_active if is_home_foul else home_active

            if not foul_players or not victim_players:
                continue

            if is_home_foul:
                match.fouls_home += 1
            else:
                match.fouls_away += 1

            # Người phạm lỗi (ưu tiên Hậu vệ và Tiền vệ phòng ngự)
            def_fouls = [p for p in foul_players if getattr(p, 'position', '') in ['CB', 'CDM', 'LB', 'RB', 'LWB', 'RWB', 'CM']]
            fowler = random.choice(def_fouls) if def_fouls else random.choice(foul_players)
            fowler_pos = getattr(fowler, 'position', 'CB')

            # Người bị phạm lỗi (ưu tiên Tiền đạo, Cánh, Hộ công)
            att_victims = [p for p in victim_players if getattr(p, 'position', '') in ['ST', 'LW', 'RW', 'CAM']]
            victim = random.choice(att_victims) if att_victims else random.choice(victim_players)
            victim_pos = getattr(victim, 'position', 'ST')

            foul_severity = random.random()
            fowler_tag = f"[{fowler_pos}] {fowler.name}"
            victim_tag = f"[{victim_pos}] {victim.name}"

            # --- 3.1: PHẠT ĐỀN 11M (PENALTY TRONG VÒNG CẤM) ---
            # Thường do hậu vệ hoặc thủ môn phạm lỗi khi ngăn chặn tiền đạo đột phá trong 16m50
            if foul_severity < 0.08 and fowler_pos in ['CB', 'LB', 'RB', 'LWB', 'RWB', 'CDM', 'GK']:
                # 35% có VAR kiểm tra lại pha phạm lỗi trong 16m50
                if random.random() < 0.35:
                    match.add_event(
                        minute,
                        f"🖥️ VAR KIỂM TRA PHẠT ĐỀN! Phút {minute}: Trọng tài tạm dừng trận đấu xem lại video xác định {fowler_tag} có phạm lỗi trong vòng cấm hay không!",
                        event_type="var_check",
                        data={"is_home": not is_home_foul, "check_type": "penalty", "decision": "confirmed", "player": victim.name}
                    )

                match.add_event(
                    minute,
                    f"⚠️ PHẠT ĐỀN 11M! Phút {minute}: {fowler_tag} ({foul_team.name}) đốn ngã {victim_tag} trong vòng cấm địa! Trọng tài dứt khoát chỉ tay vào chấm phạt đền 11m!",
                    event_type="penalty_call",
                    data={"is_home_foul": is_home_foul, "fowler": fowler.name, "victim": victim.name}
                )

                # Ưu tiên giao trách nhiệm đá phạt đền cho ST hoặc người dứt điểm tốt nhất
                st_candidates = [p for p in victim_players if getattr(p, 'position', '') in ['ST', 'CF', 'CAM']]
                taker = st_candidates[0] if st_candidates else victim
                taker_pos = getattr(taker, 'position', 'ST')
                taker_tag = f"[{taker_pos}] {taker.name}"

                gk = next((p for p in foul_players if getattr(p, 'position', '') == 'GK'), foul_players[0])
                gk_tag = f"[GK] {gk.name}"

                if is_home_foul:
                    match.shots_away += 1
                else:
                    match.shots_home += 1

                pen_styles = ['top_right', 'top_left', 'bottom_right', 'bottom_left', 'panenka']
                chosen_style = random.choice(pen_styles)
                is_pen_goal = (random.random() < 0.76)

                if is_pen_goal:
                    if is_home_foul:
                        match.away_goals += 1
                        match.target_away += 1
                    else:
                        match.home_goals += 1
                        match.target_home += 1

                    taker.goals += 1
                    style_desc = "bằng cú xúc thìa Panenka lạnh lùng" if chosen_style == 'panenka' else "găm thẳng vào góc chữ A"
                    match.add_event(
                        minute,
                        f"🎯 PENALTY VÀOOO! Phút {minute}: Trên chấm 11m, {taker_tag} {style_desc} đánh lừa thủ môn {gk_tag}! Tỉ số: {match.home_goals}-{match.away_goals}",
                        event_type="penalty_kick",
                        data={"is_home": not is_home_foul, "taker": taker.name, "gk": gk.name, "is_goal": True, "style": chosen_style}
                    )
                else:
                    if is_home_foul:
                        match.target_away += 1
                    else:
                        match.target_home += 1

                    match.add_event(
                        minute,
                        f"🧤 PENALTY KHÔNG VÀO! Phút {minute}: Cú sút phạt đền 11m của {taker_tag} đã bị thủ môn {gk_tag} xuất thần bay người cản phá thành công!",
                        event_type="penalty_kick",
                        data={"is_home": not is_home_foul, "taker": taker.name, "gk": gk.name, "is_goal": False, "style": chosen_style}
                    )

            # --- 3.2: THẺ VÀNG 🟨 ---
            elif foul_severity < 0.31:
                if fowler_pos == 'CDM':
                    reason = f"phạm lỗi chiến thuật (Tactical Foul) từ phía sau ngăn chặn pha phản công thần tốc của {victim_tag}"
                elif fowler_pos in ['LB', 'RB', 'LWB', 'RWB']:
                    reason = f"phi thân xoạc bóng sát mép đường biên đốn ngã {victim_tag}"
                elif fowler_pos == 'CB':
                    reason = f"dùng tiểu xảo kéo áo lộ liễu ngăn cản pha thoát xuống nguy hiểm của {victim_tag}"
                else:
                    reason = f"vào bóng bằng gầm giày nguy hiểm đốn ngã {victim_tag}"

                current_yellow = getattr(fowler, 'yellow_cards', 0)

                if current_yellow == 0:
                    fowler.yellow_cards = 1
                    if is_home_foul:
                        match.yellow_home += 1
                    else:
                        match.yellow_away += 1

                    match.add_event(
                        minute,
                        f"🟨 Thẻ vàng! Phút {minute}: Trọng tài rút thẻ vàng cảnh cáo {fowler_tag} ({foul_team.name}) sau pha {reason}!",
                        event_type="yellow_card",
                        data={"is_home": is_home_foul, "player": fowler.name, "team": foul_team.name}
                    )
                else:
                    fowler.yellow_cards += 1
                    fowler.red_cards = 1
                    if is_home_foul:
                        match.yellow_home += 1
                        match.red_home += 1
                    else:
                        match.yellow_away += 1
                        match.red_away += 1

                    match.add_event(
                        minute,
                        f"🟥 THẺ ĐỎ! Phút {minute}: {fowler_tag} ({foul_team.name}) nhận THẺ VÀNG THỨ 2 sau pha {reason}! Trọng tài truất quyền thi đấu, {foul_team.name} chỉ còn 10 người trên sân!",
                        event_type="red_card",
                        data={"is_home": is_home_foul, "player": fowler.name, "team": foul_team.name, "second_yellow": True}
                    )

            # --- 3.3: THẺ ĐỎ TRỰC TIẾP 🟥 ---
            elif foul_severity < 0.34 and fowler_pos in ['CB', 'CDM']:
                fowler.red_cards = 1
                if is_home_foul:
                    match.red_home += 1
                else:
                    match.red_away += 1

                red_reasons = [
                    f"phạm lỗi ác ý ngăn chặn cơ hội mười mươi khi là chốt chặn cuối cùng (Last Man Tackle) với {victim_tag}",
                    f"có pha vào bóng triệt hạ thô bạo cực kỳ nguy hiểm với {victim_tag}"
                ]
                match.add_event(
                    minute,
                    f"🟥 THẺ ĐỎ TRỰC TIẾP! Phút {minute}: {fowler_tag} ({foul_team.name}) {random.choice(red_reasons)}! {foul_team.name} tổn thất cực lớn và phải chơi thiếu người!",
                    event_type="red_card",
                    data={"is_home": is_home_foul, "player": fowler.name, "team": foul_team.name, "direct_red": True}
                )

            # --- 3.4: PHẠM LỖI THÔNG THƯỜNG (FOUL) ---
            else:
                normal_fouls = [
                    f"va chạm tranh chấp bóng bổng quyết liệt với {victim_tag}",
                    f"chèn người trái phép ở khu vực trung tuyến với {victim_tag}",
                    f"quét chân cản phá lỗi khi tranh chấp bóng 50-50 với {victim_tag}"
                ]
                match.add_event(
                    minute,
                    f"⚠️ Phạm lỗi! Phút {minute}: Trọng tài cắt còi thổi phạt {fowler_tag} ({foul_team.name}) sau pha {random.choice(normal_fouls)}. Quả đá phạt cho {victim_team.name}.",
                    event_type="foul",
                    data={"is_home": is_home_foul, "fowler": fowler.name, "victim": victim.name}
                )

        # ==========================================================
        # NHÁNH 4: PHẠT GÓC (CORNER KICK) (~12% mỗi phút)
        # ==========================================================
        elif roll < 0.63:
            is_home_corner = (random.random() < home_prob)
            att_team = home_team if is_home_corner else away_team
            def_team = away_team if is_home_corner else home_team
            att_players = home_active if is_home_corner else away_active
            def_players = away_active if is_home_corner else home_active

            if not att_players or not def_players:
                continue

            if is_home_corner:
                match.corners_home += 1
            else:
                match.corners_away += 1

            # Người thực hiện đá phạt góc (ưu tiên cánh, tiền vệ tấn công)
            taker_candidates = [p for p in att_players if getattr(p, 'position', '') in ['LW', 'RW', 'CAM', 'LM', 'RM', 'LB', 'RB', 'LWB', 'RWB']]
            taker = random.choice(taker_candidates) if taker_candidates else att_players[0]
            taker_pos = getattr(taker, 'position', 'W')
            taker_tag = f"[{taker_pos}] {taker.name}"

            # Người bật cao đón bóng trong vòng cấm (ưu tiên ST, CB, CM không chiến)
            header_candidates = [p for p in att_players if getattr(p, 'position', '') in ['ST', 'CB', 'CF', 'CM'] and p.name != taker.name]
            header_player = random.choice(header_candidates) if header_candidates else random.choice(att_players)
            header_pos = getattr(header_player, 'position', 'ST')
            header_tag = f"[{header_pos}] {header_player.name}"

            corner_side = random.choice(["top", "bottom"])

            # Tỉ lệ đánh đầu thành bàn từ phạt góc (~12%)
            is_goal_from_corner = (random.random() < 0.12)
            if is_goal_from_corner:
                if is_home_corner:
                    match.home_goals += 1
                    match.shots_home += 1
                    match.target_home += 1
                else:
                    match.away_goals += 1
                    match.shots_away += 1
                    match.target_away += 1
                header_player.goals += 1

                match.add_event(
                    minute,
                    f"⚽ VÀOOO! Phút {minute}: {taker_tag} ({att_team.name}) treo bóng góc cực kỳ chuẩn xác, {header_tag} bật cao đánh đầu dũng mãnh tung lưới đối phương! Tỉ số {match.home_goals}-{match.away_goals}",
                    event_type="goal",
                    data={
                        "is_home": is_home_corner,
                        "shooter": header_player.name,
                        "dist": 8,
                        "zone": "Phạt góc (Đánh đầu)",
                        "pos": header_pos
                    }
                )
            else:
                corner_outcomes = [
                    f"nhưng thủ môn đối phương đã băng ra đấm bóng an toàn",
                    f"cú đánh đầu của {header_tag} đưa bóng đi vọt xà ngang trong gang tấc",
                    f"trung vệ đối phương đã bật cao phá bóng giải nguy chịu quả ném biên",
                    f"hàng thủ số đông đã bọc lót giải tỏa áp lực thành công"
                ]
                match.add_event(
                    minute,
                    f"🚩 Phạt góc! Phút {minute}: {taker_tag} ({att_team.name}) thực hiện quả phạt góc câu bổng vào vòng 16m50, {random.choice(corner_outcomes)}.",
                    event_type="corner_kick",
                    data={
                        "is_home": is_home_corner,
                        "taker": taker.name,
                        "header_player": header_player.name,
                        "side": corner_side
                    }
                )

        # ==========================================================
        # NHÁNH 5: NÉM BIÊN CHIẾN THUẬT (THROW-IN) (~11% mỗi phút)
        # ==========================================================
        elif roll < 0.74:
            is_home_throw = (random.random() < home_prob)
            att_team = home_team if is_home_throw else away_team
            def_team = away_team if is_home_throw else home_team
            att_players = home_active if is_home_throw else away_active

            if not att_players:
                continue

            # Người ném biên thường là hậu vệ biên (LB, RB, LWB, RWB)
            thrower_candidates = [p for p in att_players if getattr(p, 'position', '') in ['LB', 'RB', 'LWB', 'RWB', 'LM', 'RM']]
            thrower = random.choice(thrower_candidates) if thrower_candidates else att_players[0]
            thrower_pos = getattr(thrower, 'position', 'DF')
            thrower_tag = f"[{thrower_pos}] {thrower.name}"

            # Người nhận bóng (tiền vệ hoặc tiền đạo cánh)
            receiver_candidates = [p for p in att_players if p.name != thrower.name and getattr(p, 'position', '') in ['CM', 'CAM', 'LW', 'RW', 'CDM']]
            receiver = random.choice(receiver_candidates) if receiver_candidates else att_players[1]
            receiver_pos = getattr(receiver, 'position', 'MF')
            receiver_tag = f"[{receiver_pos}] {receiver.name}"

            throw_side = "top" if thrower_pos in ['LB', 'LWB', 'LM', 'LW'] else "bottom"

            throw_descs = [
                f"ném bóng nhanh cho {receiver_tag} ban bật đập nhả thoát pressing dọc hành lang biên",
                f"thực hiện quả ném biên mạnh (Long Throw-in) thẳng vào nách vòng cấm địa",
                f"phối hợp ném biên chiến thuật giữ quyền kiểm soát bóng"
            ]
            match.add_event(
                minute,
                f"📐 Ném biên! Phút {minute}: {thrower_tag} ({att_team.name}) {random.choice(throw_descs)}.",
                event_type="throw_in",
                data={
                    "is_home": is_home_throw,
                    "thrower": thrower.name,
                    "receiver": receiver.name,
                    "side": throw_side
                }
            )

        # ==========================================================
        # NHÁNH 6: ĐÁ PHẠT TRỰC TIẾP HÀNG RÀO (FREE KICK) (~8% mỗi phút)
        # ==========================================================
        elif roll < 0.82:
            is_home_fk = (random.random() < home_prob)
            att_team = home_team if is_home_fk else away_team
            def_team = away_team if is_home_fk else home_team
            att_players = home_active if is_home_fk else away_active
            def_players = away_active if is_home_fk else home_active

            if not att_players or not def_players:
                continue

            # Chuyên gia sút phạt (CAM, ST, RW, LW, CM)
            fk_takers = [p for p in att_players if getattr(p, 'position', '') in ['CAM', 'ST', 'RW', 'LW', 'CM']]
            taker = random.choice(fk_takers) if fk_takers else att_players[0]
            taker_pos = getattr(taker, 'position', 'CAM')
            taker_tag = f"[{taker_pos}] {taker.name}"

            fk_dist = random.randint(20, 28)
            gk = next((p for p in def_players if getattr(p, 'position', '') == 'GK'), def_players[0])
            gk_tag = f"[GK] {gk.name}"

            # Tỉ lệ thành bàn từ đá phạt hàng rào (~14%)
            is_fk_goal = (random.random() < 0.14)
            if is_fk_goal:
                if is_home_fk:
                    match.home_goals += 1
                    match.shots_home += 1
                    match.target_home += 1
                else:
                    match.away_goals += 1
                    match.shots_away += 1
                    match.target_away += 1
                taker.goals += 1

                match.add_event(
                    minute,
                    f"⚽ SIÊU PHẨM ĐÁ PHẠT! Phút {minute}: Từ cự ly {fk_dist}m, {taker_tag} ({att_team.name}) vẽ nên đường cong cầu vồng tuyệt mỹ qua hàng rào găm thẳng vào góc chữ A! Tỉ số {match.home_goals}-{match.away_goals}",
                    event_type="goal",
                    data={
                        "is_home": is_home_fk,
                        "shooter": taker.name,
                        "dist": fk_dist,
                        "zone": f"Đá phạt hàng rào ({fk_dist}m)",
                        "pos": taker_pos
                    }
                )
            else:
                if is_home_fk:
                    match.shots_home += 1
                else:
                    match.shots_away += 1

                fk_reasons = [
                    f"đưa bóng lượn qua hàng rào nhưng chệch cột dọc trong gang tấc",
                    f"bị thủ môn {gk_tag} bay người đấm bóng chịu phạt góc",
                    f"đập trúng hàng rào chắn bật ngược trở lại"
                ]
                match.add_event(
                    minute,
                    f"🎯 Đá phạt! Phút {minute}: {taker_tag} ({att_team.name}) sút phạt hàng rào cự ly {fk_dist}m, {random.choice(fk_reasons)}.",
                    event_type="free_kick",
                    data={
                        "is_home": is_home_fk,
                        "taker": taker.name,
                        "dist": fk_dist
                    }
                )

    return match


def simulate_half(match, half_number, home_tactic="Can bang", away_tactic="Can bang"):
    start_min = 1 if half_number == 1 else 46
    end_min = 45 if half_number == 1 else 90
    return run_minutes(match, start_min, end_min, home_tactic, away_tactic)


def simulate_match(home_team, away_team, round_number=1, home_tactic="Can bang", away_tactic="Can bang"):
    from football.classes import MatchOld
    match = MatchOld(home_team, away_team, round_number)
    match = simulate_half(match, 1, home_tactic, away_tactic)
    match.add_event(45, f"⏱️ Kết thúc hiệp 1! Tỉ số {match.home_goals}-{match.away_goals}")
    match = simulate_half(match, 2, home_tactic, away_tactic)
    match.add_event(90, f"⏱️ Kết thúc trận đấu! Tỉ số chung cuộc {match.home_goals}-{match.away_goals}")
    match.finished = True
    return match