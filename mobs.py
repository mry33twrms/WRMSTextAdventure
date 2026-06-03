class mob:
    def __init__(self, name, hp, attack):
        self.name = name
        self.hp = hp
        self.attack = attack

    def take_damage(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            print(f"{self.name} has been defeated!")
        else:
            print(f"{self.name} has {self.hp} HP remaining.")

    def deal_damage(self):
        return self.attack
    
# goblin = mob("Goblin", 10, 4)
# alien = mob("Christopher the Alien", 82, 9)
# parabola = mob("Parabola", 100, 12)


mob_dict = {
    "Goblin" : {"hp": 10, "attack": 4, "weakness": "Fire"},
    "Hydrogen Elemental" : {"hp": 82, "attack": 15, "weakness": "Oxygen"},
    "Parabola" : {"hp": 100, "attack": 20, "weakness": "Calculator"},
    "Insane Doctor" : {"hp": 35, "attack": 8, "weakness": "Therapy"},
    "Possessed Canes" : {"hp": 20, "attack": 6,},
    "Weaners & Beans" : {"hp": 15, "attack": 5,},
    "Beholder": {"hp": 125, "attack": 25, "weakness": "Damaging the Eye"},
    "Orc Guard": {"hp": 10, "attack": 5, "weakness": "Very Stupid"}
}