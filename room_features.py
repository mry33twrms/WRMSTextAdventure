'''

Room features and their systems are defined here. Each room can have a list of features, which are special interactive elements in the room. 
Features can be things like fishing holes, ores to mine, or other unique interactions.

'''

features_dict = {
    "respawn point" : {
        "name" : "Respawn Point",
        "desc" : "A magical point where players can respawn after death.",
        "action" : "respawn",
        "respawn_time" : 60,  # seconds
    },
    "fishing hole" : {
        "name" : "Fishing Hole",
        "desc" : "A small pond or body of water where you can fish.",
        "action" : "fish",
        "success_rate" : 0.5,
        "reward" : "fish",
        "reward_amount" : 1,
        "cooldown" : 60,  # seconds
    },
    "ore vein" : {
        "name" : "Ore Vein",
        "desc" : "A vein of ore that can be mined for resources.",
        "action" : "mine",
        "success_rate" : 0.7,
        "reward" : "ore",
        "reward_amount" : 1,
        "cooldown" : 120,  # seconds
    },
    "herb patch" : {
        "name" : "Herb Patch",
        "desc" : "A patch of herbs that can be harvested for ingredients.",
        "action" : "harvest",
        "success_rate" : 0.6,
        "reward" : "herb",
        "reward_amount" : 1,
        "cooldown" : 90,  # seconds
    },
}

# Fishing-related commands and logic

async def cmd_fish(player, _args, _gs):
    # Placeholder for fishing command implementation
    pass

# Mining-related commands and logic

async def cmd_mine(player, _args, _gs):
    # Placeholder for mining command implementation
    pass

# Gathering plants command and logic
async def cmd_harvest(player, _args, _gs):
    # Placeholder for gathering plants command implementation
    pass

