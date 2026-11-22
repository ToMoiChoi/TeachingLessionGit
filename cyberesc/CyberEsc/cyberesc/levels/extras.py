"""Quái mới bổ sung cho từng màn (thêm sau khi file lvX.py đã tạo màn chơi).

Mỗi mục: (loại, x) hoặc (loại, x, y). Loại: kami, sniper, tele, mothership.
"""

LEVEL_EXTRAS = {
    2: [("kami", 1250)],
    3: [("kami", 950), ("sniper", 1600)],
    4: [("sniper", 1150), ("kami", 1550)],
    5: [("kami", 650), ("sniper", 1450), ("tele", 1000, 200)],
    6: [("tele", 800, 200), ("kami", 1400), ("mothership", 1900, 60)],
    7: [("kami", 500), ("kami", 1600), ("sniper", 1150), ("tele", 1900, 180)],
    8: [("sniper", 1500), ("tele", 1000, 190), ("kami", 1200)],
    9: [("kami", 850), ("sniper", 1480), ("tele", 1750, 190)],
    10: [("kami", 920), ("sniper", 1520), ("tele", 1280, 180)],
    11: [("sniper", 950), ("sniper", 1720), ("tele", 1360, 170), ("kami", 1580)],
    12: [("tele", 900, 180), ("sniper", 1460), ("kami", 1680), ("mothership", 1920, 55)],
    13: [("kami", 680), ("kami", 1220), ("kami", 1740), ("sniper", 1460), ("tele", 1980, 175)],
    14: [("sniper", 1120), ("tele", 1520, 170), ("kami", 940), ("kami", 1700)],
    15: [("kami", 720), ("sniper", 1160), ("tele", 1480, 165), ("sniper", 1880), ("tele", 2060, 170)],
    16: [("kami", 960), ("sniper", 1420), ("tele", 1180, 175), ("tele", 1780, 165)],
}

# Vị trí cột checkpoint giữa màn (16 màn)
CHECKPOINT_X = {lvl: 1200 for lvl in range(1, 17)}
