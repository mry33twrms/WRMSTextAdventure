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
    "goblin" : {"hp": 10, "attack": 4, "weakness": "Fire"},
    "hydrogen elemental" : {"hp": 82, "attack": 15, "weakness": "Oxygen"},
    "parabola" : {"hp": 100, "attack": 20, "weakness": "Calculator"},
    "insane doctor" : {"hp": 35, "attack": 8, "weakness": "Therapy"},
    "possessed canes" : {"hp": 20, "attack": 6,},
    "weaners & beans" : {"hp": 15, "attack": 5,},
    "beholder": {"hp": 125, "attack": 25, "weakness": "Damaging the Eye"},
    "orc guard": {"hp": 10, "attack": 5, "weakness": "Very Stupid"}
}