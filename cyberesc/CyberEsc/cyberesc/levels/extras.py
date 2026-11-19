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
}

# Vị trí cột checkpoint giữa màn
CHECKPOINT_X = {lvl: 1200 for lvl in range(1, 9)}
