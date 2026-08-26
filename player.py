from config import (
    DAMAGE_PER_STR, CRIT_POWER_PER_STR,
    EVASION_PER_AGI, CRIT_CHANCE_PER_AGI,
    MAGIC_DAMAGE_PER_INT, MAGIC_RESIST_PER_INT,
    HP_PER_VIT, BASE_HP, BASE_ATTACK,
    MP_PER_INT, BASE_MP,
    STARTING_STAT, STARTING_LEVEL,
)


class Player:
    def __init__(self, name, current_room, writer, gold=0, inventory=None, max_inventory=10):
        self.name = name
        self.current_room = current_room
        self.writer = writer
        self.quitting = False
        self.talking_to = None
        self.pending_transaction = None

        # Economy / inventory
        self.gold = gold
        self.inventory = inventory or []
        self.max_inventory = max_inventory

        # Primary stats
        self.strength     = STARTING_STAT
        self.agility      = STARTING_STAT
        self.intelligence = STARTING_STAT
        self.vitality     = STARTING_STAT

        # Level / XP
        self.level       = STARTING_LEVEL
        self.xp          = 0
        self.stat_points = 0

        # Bonus stats accumulated from equipped items
        self.bonus_attack  = 0
        self.bonus_defense = 0

        # Elemental resistances
        self.fire_resist  = 0
        self.ice_resist   = 0
        self.shock_resist = 0

        # Account
        self.role       = "player"  # "player" | "admin" — set from DB on login
        self.reset_mode = None      # None | {"target": name, "step": "new"|"confirm", "pending": pw}

        # Accessibility
        self.concise_mode  = False  # when True, skip room descriptions on revisits
        self.visited_rooms = set()  # room keys seen at least once

        # Party / messaging
        self.party       = None  # Party object, or None
        self.last_sender = None  # name of last player who sent a tell

        # Following
        self.following = None  # name of player being followed, or None
        self.followers = set() # set of player names following this player

        # Combat state
        self.in_combat   = False
        self.combat_room = None

        # Quests
        self.quests             = {}   # quest_id -> {name, desc, status}
        self.quest_items        = []   # quest item keys (no inventory slot used)
        self.received_npc_items = set() # item keys given by NPCs (one-time gifts)

        # Respawn
        self.respawn_point = "front admin"

        # Equipment slots
        self.equipped_items = {
            "head":      None,
            "body":      None,
            "legs":      None,
            "feet":      None,
            "gloves":    None,
            "weapon":    None,
            "shield":    None,
            "accessory": None,
            "tool":      None,
        }

        # Derive all combat stats from primary stats + bonuses
        self.hp = 0  # placeholder; recalculate sets max_hp/max_mp, then we fill
        self.mp = 0
        self.recalculate_stats()
        self.hp = self.max_hp
        self.mp = self.max_mp

    def recalculate_stats(self):
        """Recompute all derived stats from primary stats and equipment bonuses."""
        self.max_hp      = BASE_HP + self.vitality     * HP_PER_VIT
        self.max_mp      = BASE_MP + self.intelligence * MP_PER_INT
        self.attack      = BASE_ATTACK + self.strength * DAMAGE_PER_STR + self.bonus_attack
        self.defense     = self.bonus_defense

        self.crit_chance  = self.agility      * CRIT_CHANCE_PER_AGI
        self.crit_power   = self.strength     * CRIT_POWER_PER_STR
        self.evasion      = self.agility      * EVASION_PER_AGI
        self.magic_damage = self.intelligence * MAGIC_DAMAGE_PER_INT
        self.magic_resist = self.intelligence * MAGIC_RESIST_PER_INT

        # Clamp current HP/MP to new max
        if hasattr(self, "hp"):
            self.hp = min(self.hp, self.max_hp)
        if hasattr(self, "mp"):
            self.mp = min(self.mp, self.max_mp)

    async def send(self, msg):
        try:
            self.writer.write((msg + "\n").encode())
            await self.writer.drain()
        except (ConnectionResetError, BrokenPipeError, OSError):
            pass
