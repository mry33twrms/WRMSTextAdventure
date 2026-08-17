players = {}         # name -> Player instance
room_mobs = {}       # room_name -> list of live mob instances
combat_sessions = {} # room_name -> CombatSession
unlocked_exits = set() # set of (room_name, direction) that are temporarily unlocked
