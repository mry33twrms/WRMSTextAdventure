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


