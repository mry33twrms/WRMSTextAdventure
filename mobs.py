from config import (
    DAMAGE_PER_STR, CRIT_POWER_PER_STR,
    EVASION_PER_AGI, CRIT_CHANCE_PER_AGI,
    HP_PER_VIT, BASE_HP, BASE_ATTACK,
)


class mob:
    def __init__(self, name, info):
        self.name = name
        self.strength = info.get("strength", 1)
        self.agility  = info.get("agility", 1)
        self.vitality = info.get("vitality", 1)
        self.defense  = info.get("defense", 0)

        self.max_hp      = BASE_HP + self.vitality * HP_PER_VIT
        self.hp          = self.max_hp
        self.attack      = BASE_ATTACK + self.strength * DAMAGE_PER_STR
        self.crit_chance = self.agility * CRIT_CHANCE_PER_AGI
        self.crit_power  = self.strength * CRIT_POWER_PER_STR
        self.evasion     = self.agility * EVASION_PER_AGI

    def take_damage(self, damage):
        self.hp -= damage
        return self.hp <= 0


mob_dict = {
    "goblin": {
        "name": "Goblin",
        "desc": "A small, green creature.",
        "strength": 2,
        "agility":  2,
        "vitality": 1,
        "defense":  0,
        "weakness": "Fire",
        "gold": 5,
        "xp": 10,
        "respawn_time": 60,
        "loot_chance": 0.5,
        "loot": ["leather", "cloth pants", "cloth shirt", "cloth shoes", "cloth gloves", "apple", "bread"],
    },
    "troll": {
        "name": "Troll",
        "desc": "A large, brutish creature.",
        "strength": 8,
        "agility":  1,
        "vitality": 5,
        "defense":  3,
        "weakness": "Fire",
        "gold": 15,
        "xp": 30,
        "respawn_time": 60,
        "loot_chance": 0.5,
        "loot": ["leather", "cloth pants", "cloth shirt", "cloth shoes", "cloth gloves", "apple", "bread"],
    },
    "skeleton": {
        "name": "Skeleton",
        "desc": "A reanimated skeleton.",
        "strength": 4,
        "agility":  3,
        "vitality": 3,
        "defense":  1,
        "weakness": "Blunt Weapons",
        "gold": 10,
        "xp": 20,
        "respawn_time": 60,
        "loot_chance": 0.5,
        "loot": ["leather", "cloth pants", "cloth shirt", "cloth shoes", "cloth gloves", "apple", "bread"],
    },
    "orc guard": {
        "name": "Orc Guard",
        "desc": "A brute-like orc with a shield.",
        "strength": 5,
        "agility":  2,
        "vitality": 4,
        "defense":  3,
        "weakness": "Very Stupid",
        "gold": 10,
        "xp": 20,
        "respawn_time": 60,
        "loot_chance": 0.5,
        "loot": ["leather", "cloth pants", "cloth shirt", "cloth shoes", "cloth gloves", "apple", "bread"],
    },
}


'''
Evan's ones:
    "hydro elemental": {"name" : "Hydro Elementaal", "desc": "A powerful water-based entity.", "hp": 82,  "attack": 15, "weakness": "Oxygen","gold": 10, "respawn_time": 60},
    "parabola":           {"name" : "Parabola", "desc": "A mysterious flying object.", "hp": 100, "attack": 20, "weakness": "Calculator","gold": 15, "respawn_time": 60},
    "insane doctor":      {"name" : "Insane Doctor", "desc": "A deranged medical professional.", "hp": 35,  "attack": 8,  "weakness": "Therapy", "gold": 8, "respawn_time": 60},
    "possessed cane":     {"name" : "Possessed Cane", "desc": "A orientation and mobility tool with a malevolent spirit.", "hp": 20,  "attack": 6,"gold": 6, "respawn_time": 60},
    "weiners & beans":    {"name" : "Weiners & Beans", "desc": "A gelatinous mass.", "hp": 15,  "attack": 5, "gold": 5, "respawn_time": 60},
    "beholder":           {"name" : "Beholder", "desc": "A giant eye with a malevolent presence.", "hp": 125, "attack": 25, "weakness": "Damaging the Eye", "gold": 25, "respawn_time": 60},
'''
