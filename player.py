class Player:
    def __init__(self, name, current_room, writer, attack=5, hp=20, gold=0, inventory=None, max_inventory=10, max_hp=20, defense=0):
        self.name = name
        self.current_room = current_room
        self.writer = writer
        self.quitting = False
        self.attack = attack
        self.hp = hp
        self.gold = gold
        self.inventory = inventory or []
        self.max_inventory = max_inventory
        self.max_hp = max_hp
        self.defense = defense
        self.equipped_items = {
            "head": None,
            "body": None,
            "legs": None,
            "feet": None,
            "weapon": None,
            "shield": None,
            "accessory": None,
            "tool": None }
        


    async def send(self, msg):
        try:
            self.writer.write((msg + "\n").encode())
            await self.writer.drain()
        except (ConnectionResetError, BrokenPipeError, OSError):
            pass
