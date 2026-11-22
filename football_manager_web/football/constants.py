# -*- coding: utf-8 -*-
"""
football.constants - Tập trung toàn bộ hằng số dữ liệu game (vị trí, sơ đồ, giải đấu, học viện).
"""

POSITIONS = ["GK", "CB", "LB", "RB", "LWB", "RWB", "CDM", "CM", "LM", "RM", "CAM", "LW", "RW", "ST"]

FIRST_NAMES = [
    "John", "Ethan", "Michael", "David", "James", "Robert", "Thomas", "Daniel", "Paul", "Mark",
    "Steven", "Andrew", "Kenneth", "Joshua", "Kevin", "Brian", "George", "Edward", "Ronald", "Timothy",
    "Jason", "Jeffrey", "Ryan", "Jacob", "Gary", "Nicholas", "Eric", "Jonathan", "Stephen", "Larry",
    "Justin", "Scott", "Brandon", "Benjamin", "Samuel", "Raymond", "Gregory", "Frank", "Alexander",
    "Patrick", "Jack", "Dennis", "Jerry", "Tyler", "Aaron", "Jose", "Nathan", "Adam", "Henry", "Zachary"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
    "Hernandez", "Lopez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee",
    "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
    "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts", "Turner"
]

FORMATION_POSITIONS = {
    '4-3-3': ['GK', 'LB', 'CB', 'CB', 'RB', 'LW', 'CM', 'CM', 'CM', 'RW', 'ST'],
    '4-2-3-1': ['GK', 'LB', 'CB', 'CB', 'RB', 'CDM', 'CDM', 'LW', 'CAM', 'RW', 'ST'],
    '4-4-2': ['GK', 'LB', 'CB', 'CB', 'RB', 'LM', 'CM', 'CM', 'RM', 'ST', 'ST'],
    '4-3-2-1': ['GK', 'LB', 'CB', 'CB', 'RB', 'CDM', 'CM', 'CM', 'CAM', 'CAM', 'ST'],
    '3-4-3': ['GK', 'CB', 'CB', 'CB', 'LM', 'CM', 'CM', 'RM', 'LW', 'RW', 'ST'],
    '3-5-2': ['GK', 'CB', 'CB', 'CB', 'LWB', 'CDM', 'CM', 'CM', 'RWB', 'ST', 'ST'],
    '5-3-2': ['GK', 'LWB', 'CB', 'CB', 'CB', 'RWB', 'CM', 'CM', 'CM', 'ST', 'ST'],
    '5-4-1': ['GK', 'LWB', 'CB', 'CB', 'CB', 'RWB', 'LM', 'CM', 'CM', 'RM', 'ST'],
}

SCOUT_HUBS = {
    "vietnam": {
        "name": "Học Viện Trẻ Việt Nam", "cost": 150000,
        "pot_min": 72, "pot_max": 88, "origin": "Học Viện JMG / PVF",
        "first_names": ["Minh", "Quang", "Tuấn", "Hoàng", "Duy", "Đức", "Văn", "Công", "Hùng", "Hải", "Bảo", "Long"],
        "last_names": ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Đặng", "Bùi", "Đỗ", "Hồ"]
    },
    "south_america": {
        "name": "Lò Đào Tạo Nam Mỹ", "cost": 450000,
        "pot_min": 82, "pot_max": 95, "origin": "Santos / Boca Juniors",
        "first_names": ["Lucas", "Mateo", "Gabriel", "Thiago", "Enzo", "Felipe", "Rodrigo", "Joao", "Diego", "Julian"],
        "last_names": ["Silva", "Santos", "Oliveira", "Rodriguez", "Martinez", "Alvarez", "Fernandez", "Gomez", "Costa"]
    },
    "europe": {
        "name": "Lò Đào Tạo Châu Âu (Wonderkids)", "cost": 850000,
        "pot_min": 88, "pot_max": 99, "origin": "La Masia / Carrington / Ajax",
        "first_names": ["Leo", "Lamine", "Jude", "Gavi", "Pedri", "Kylian", "Erling", "Florian", "Arda", "Jamal"],
        "last_names": ["Yamal", "Bellingham", "Musiala", "Wirtz", "Guler", "Davies", "Camavinga", "Mainoo", "Endrick"]
    },
    "africa": {
        "name": "Học Viện Thể Lực Châu Phi", "cost": 300000,
        "pot_min": 76, "pot_max": 92, "origin": "Right to Dream / ASEC",
        "first_names": ["Victor", "Sadio", "Mo", "Achraf", "Amad", "Kudus", "Osimhen", "Bissouma", "Pape"],
        "last_names": ["Diallo", "Sarr", "Toure", "Kone", "Mensah", "Traore", "Camara", "Diop", "Cisse"]
    }
}

LEAGUE_OPPONENTS = {
    "Hang 2": [
        {"name": "Bình Phước FC", "formation": "4-3-3", "tactic": "Tan cong"},
        {"name": "PVF-CAND", "formation": "4-2-3-1", "tactic": "Can bang"},
        {"name": "Phù Đổng Ninh Bình", "formation": "5-3-2", "tactic": "Phong thu"},
        {"name": "Bà Rịa Vũng Tàu", "formation": "4-3-3", "tactic": "Can bang"},
        {"name": "Long An FC", "formation": "4-2-3-1", "tactic": "Phong thu"},
        {"name": "Đồng Tháp FC", "formation": "5-3-2", "tactic": "Phong thu"},
        {"name": "Huế FC", "formation": "4-3-3", "tactic": "Can bang"},
        {"name": "Hòa Bình FC", "formation": "4-2-3-1", "tactic": "Can bang"},
        {"name": "Đồng Nai FC", "formation": "5-3-2", "tactic": "Phong thu"}
    ],
    "Hang 1": [
        {"name": "Công An Hà Nội", "formation": "4-3-3", "tactic": "Tan cong"},
        {"name": "Thép Xanh Nam Định", "formation": "4-2-3-1", "tactic": "Tan cong"},
        {"name": "Hà Nội FC", "formation": "4-3-3", "tactic": "Can bang"},
        {"name": "Thể Công Viettel", "formation": "5-3-2", "tactic": "Phong thu"},
        {"name": "Becamex Bình Dương", "formation": "4-2-3-1", "tactic": "Can bang"},
        {"name": "Hoàng Anh Gia Lai", "formation": "4-3-3", "tactic": "Tan cong"},
        {"name": "Hải Phòng FC", "formation": "4-2-3-1", "tactic": "Can bang"},
        {"name": "Sông Lam Nghệ An", "formation": "5-3-2", "tactic": "Phong thu"},
        {"name": "SHB Đà Nẵng", "formation": "4-3-3", "tactic": "Can bang"}
    ],
    "Champions League": [
        {"name": "Real Madrid", "formation": "4-3-3", "tactic": "Tan cong"},
        {"name": "Manchester City", "formation": "4-2-3-1", "tactic": "Tan cong"},
        {"name": "Bayern Munich", "formation": "4-2-3-1", "tactic": "Tan cong"},
        {"name": "Paris Saint-Germain", "formation": "4-3-3", "tactic": "Tan cong"},
        {"name": "Arsenal FC", "formation": "4-3-3", "tactic": "Can bang"},
        {"name": "Inter Milan", "formation": "5-3-2", "tactic": "Phong thu"},
        {"name": "Barcelona", "formation": "4-3-3", "tactic": "Tan cong"},
        {"name": "Liverpool FC", "formation": "4-3-3", "tactic": "Tan cong"}
    ]
}
