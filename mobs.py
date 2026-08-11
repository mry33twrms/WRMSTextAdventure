import random

class mob:
    def __init__(self, name, hp, attack):
        self.name = name
        self.hp = hp
        self.attack = attack

    def take_damage(self, damage):
        self.hp -= damage
        return self.hp <= 0  # True if defeated

    def deal_damage(self):
        return random.randint(1, self.attack)


mob_dict = {
    "goblin":             {"name" : "Goblin", "desc": "A small, green creature.", "hp": 10,  "attack": 4,  "weakness": "Fire","gold": 5, "respawn_time": 60},
    "hydro elemental": {"name" : "Hydro Elementaal", "desc": "A powerful water-based entity.", "hp": 82,  "attack": 15, "weakness": "Oxygen","gold": 10, "respawn_time": 60},
    "parabola":           {"name" : "Parabola", "desc": "A mysterious flying object.", "hp": 100, "attack": 20, "weakness": "Calculator","gold": 15, "respawn_time": 60},
    "insane doctor":      {"name" : "Insane Doctor", "desc": "A deranged medical professional.", "hp": 35,  "attack": 8,  "weakness": "Therapy", "gold": 8, "respawn_time": 60},
    "possessed cane":     {"name" : "Possessed Cane", "desc": "A orientation and mobility tool with a malevolent spirit.", "hp": 20,  "attack": 6,"gold": 6, "respawn_time": 60},
    "weiners & beans":    {"name" : "Weiners & Beans", "desc": "A gelatinous mass.", "hp": 15,  "attack": 5, "gold": 5, "respawn_time": 60},
    "beholder":           {"name" : "Beholder", "desc": "A giant eye with a malevolent presence.", "hp": 125, "attack": 25, "weakness": "Damaging the Eye", "gold": 25, "respawn_time": 60},
    "orc guard":          {"name" : "Orc Guard", "desc": "A brute-like orc with a shield.", "hp": 10,  "attack": 5,  "weakness": "Very Stupid", "gold": 3, "respawn_time": 60},
}
