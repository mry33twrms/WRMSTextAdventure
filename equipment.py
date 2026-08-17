# armor

armor_dict = {
    
    "leather" : {
        "name" : "Leather Armor",
        "desc" : "Basic leather armor for protection.",
        "defense" : 4,
        "price" : 20,
        "tier": 2
    },

    "chainmail" : {
        "name" : "Chainmail Armor",
        "desc" : "A set of interlocking metal rings for protection.",
        "defense" : 7,
        "price" : 50,
        "tier": 2
    },

    "plate" : {
        "name" : "Plate Armor",
        "desc" : "Heavy metal armor for maximum protection.",
        "defense" : 10,
        "price" : 100,
        "tier": 2
    },

    "cloth shirt" : {
        "name" : "Cloth Shirt",
        "desc" : "A simple cloth shirt. Barely any protection.",
        "defense" : 1,
        "price" : 3,
        "tier": 1
    },

    "cardboard" : {
        "name" : "Cardboard Armor",
        "desc" : "A makeshift armor made from cardboard. Not very effective.",
        "defense" : 1,
        "price" : 5,
        "tier": 2
    },  
}

# boots

boots_dict = {
    
    "leather boots" : {
        "name" : "Leather Boots",
        "desc" : "Basic leather boots for protection.",
        "defense" : 2,
        "price" : 15,
        "tier": 2
    },

    "steel boots" : {
        "name" : "Steel Boots",
        "desc" : "Heavy steel boots for maximum protection.",
        "defense" : 5,
        "price" : 40,
        "tier": 2
    },

    "cloth shoes" : {
        "name" : "Cloth Shoes",
        "desc" : "Lightweight cloth shoes for minimal protection.",
        "defense" : 1,
        "price" : 5,
        "tier": 2
    },

    "cardboard shoes" : {
        "name" : "Cardboard Shoes",
        "desc" : "A makeshift footwear made from cardboard. Not very effective.",
        "defense" : 0,
        "price" : 2,
        "tier": 2
    },  
}

# gloves

gloves_dict = {
    
    "leather gloves" : {
        "name" : "Leather Gloves",
        "desc" : "Basic leather gloves for protection.",
        "defense" : 2,
        "price" : 10,
        "tier": 2
    },

    "steel gauntlets" : {
        "name" : "Steel Gauntlets",
        "desc" : "Heavy steel gauntlets for maximum protection.",
        "defense" : 5,
        "price" : 30,
        "tier": 2
    },

    "cloth gloves" : {
        "name" : "Cloth Gloves",
        "desc" : "Lightweight cloth gloves for minimal protection.",
        "defense" : 1,
        "price" : 5,
        "tier": 2
    },

    "cardboard gloves" : {
        "name" : "Cardboard Gloves",
        "desc" : "A makeshift gloves made from cardboard. Not very effective.",
        "defense" : 0,
        "price" : 2,
        "tier": 2
    },  
}

# helmets

helmets_dict = {
    
    "leather helmet" : {
        "name" : "Leather Helmet",
        "desc" : "Basic leather helmet for protection.",
        "defense" : 2,
        "price" : 15,
        "tier": 2
    },

    "steel helmet" : {
        "name" : "Steel Helmet",
        "desc" : "Heavy steel helmet for maximum protection.",
        "defense" : 5,
        "price" : 40,
        "tier": 2
    },

    "cloth hat" : {
        "name" : "Cloth Hat",
        "desc" : "Lightweight cloth hat for minimal protection.",
        "defense" : 1,
        "price" : 5,
        "tier": 2
    },

    "cardboard hat" : {
        "name" : "Cardboard Hat",
        "desc" : "A makeshift hat made from cardboard. Not very effective.",
        "defense" : 0,
        "price" : 2,
        "tier": 2
    },  
}

legs_dict = {
    
    "leather pants" : {
        "name" : "Leather Pants",
        "desc" : "Basic leather pants for protection.",
        "defense" : 2,
        "price" : 15,
        "tier": 2
    },

    "steel greaves" : {
        "name" : "Steel Greaves",
        "desc" : "Heavy steel greaves for maximum protection.",
        "defense" : 5,
        "price" : 40,
        "tier": 2
    },

    "cloth pants" : {
        "name" : "Cloth Pants",
        "desc" : "Lightweight cloth pants for minimal protection.",
        "defense" : 1,
        "price" : 5,
        "tier": 2
    },

    "cardboard pants" : {
        "name" : "Cardboard Pants",
        "desc" : "A makeshift pants made from cardboard. Not very effective.",
        "defense" : 0,
        "price" : 2,
        "tier": 2
    },  
}

consumables_dict = {

# potions

    "health potion" : {
        "name" : "Health Potion",
        "desc" : "A potion that restores 10 HP.",
        "heal" : 10,
        "price" : 15
    },
    "mana potion" : {
        "name" : "Mana Potion",
        "desc" : "A potion that restores 10 MP.",
        "mana" : 10,
        "price" : 15
    },
    "strength potion" : {
        "name" : "Strength Potion",
        "desc" : "A potion that increases attack by 2 for 5 minutes.",
        "attack" : 2,
        "duration" : 300,
        "price" : 25
    },
    "defense potion" : {
        "name" : "Defense Potion",
        "desc" : "A potion that increases defense by 2 for 5 minutes.",
        "defense" : 2,
        "duration" : 300,
        "price" : 25
    },
    "wealth potion" : {
        "name" : "Wealth Potion",
        "desc" : "A potion that increases gold gain by 50% for 5 minutes.",
        "gold" : 0.5,
        "duration" : 300,
        "price" : 30
    },
    "experience potion" : {
        "name" : "Experience Potion",
        "desc" : "A potion that increases experience gain by 50% for 5 minutes.",
        "experience" : 0.5,
        "duration" : 300,
        "price" : 30
    },

    # food
    "apple" : {
        "name" : "Apple",
        "desc" : "A fresh apple that restores 5 HP.",
        "heal" : 5,
        "price" : 5,
        "tier": 1
    },

    "bread" : {
        "name" : "Bread",
        "desc" : "A loaf of bread that restores 10 HP.",
        "heal" : 10,
        "price" : 10,
        "tier": 1
    },

    # recall scroll
    "recall scroll" : {
        "name" : "Recall Scroll",
        "desc" : "A scroll that allows you to teleport back to the starting area.",
        "price" : 50,
        "tier": 2
    },
}

tools_dict = {
    "lockpick" : {
        "name" : "Lockpick",
        "desc" : "A small tool used to pick locks.",
        "price" : 10,
        "tier": 2
    },
    "torch" : {
        "name" : "Torch",
        "desc" : "A wooden torch that can be used to light up dark areas.",
        "price" : 5,
        "tier": 2
    },
    "rope" : {
        "name" : "Rope",
        "desc" : "A sturdy rope that can be used for climbing or tying things.",
        "price" : 15,
        "tier": 2
    },
    "shovel" : {
        "name" : "Shovel",
        "desc" : "A tool used for digging.",
        "price" : 20,
        "tier": 2
    },
    "pickaxe" : {
        "name" : "Pickaxe",
        "desc" : "A tool used for mining.",
        "price" : 25,
        "tier": 2
    },
    "fishing rod" : {
        "name" : "Fishing Rod",
        "desc" : "A tool used for fishing.",
        "price" : 30,
        "tier": 2
    },
}

materials_dict = {
    "iron ore" : {
        "name" : "Iron Ore",
        "desc" : "A chunk of raw iron ore.",
        "price" : 10,
        "tier": 2
    },
    "copper ore" : {
        "name" : "Copper Ore",
        "desc" : "A chunk of raw copper ore.",
        "price" : 8,
        "tier": 2
    },
    "gold ore" : {
        "name" : "Gold Ore",
        "desc" : "A chunk of raw gold ore.",
        "price" : 20,
        "tier": 2
    },
    "silver ore" : {
        "name" : "Silver Ore",
        "desc" : "A chunk of raw silver ore.",
        "price" : 15,
        "tier": 2
    },
    "wood logs" : {
        "name" : "Wood Logs",
        "desc" : "A stack of wood logs.",
        "price" : 5,
        "tier": 2
    },
    "stone" : {
        "name" : "Stone",
        "desc" : "A chunk of stone.",
        "price" : 1,
        "tier": 1
    },
    "herbs" : {
        "name" : "Herbs",
        "desc" : "A bundle of medicinal herbs.",
        "price" : 5,
        "tier": 1
    },
    "fish" : {
        "name" : "Fish",
        "desc" : "A freshly caught fish.",
        "price" : 10,
        "tier": 1
    },
    "ore" : {
        "name" : "Ore",
        "desc" : "A chunk of raw ore.",
        "price" : 10,
        "tier": 1
    },
    "cloth" : {
        "name" : "Cloth",
        "desc" : "A piece of cloth.",
        "price" : 5,
        "tier": 1
    },
    "leather" : {
        "name" : "Leather",
        "desc" : "A piece of tanned leather.",
        "price" : 15,
        "tier": 1
    },
    "paper" : {
        "name" : "Paper",
        "desc" : "A sheet of paper.",
        "price" : 1,
        "tier": 1
    },
}

quest_items_dict = {
    "ancient artifact" : {
        "name" : "Ancient Artifact",
        "desc" : "A mysterious artifact from an ancient civilization.",
        "price" : 100,
        "tier": 3
    },
    "magic crystal" : {
        "name" : "Magic Crystal",
        "desc" : "A crystal imbued with magical energy.",
        "price" : 150,
        "tier": 3
    },
    "rare gem" : {
        "name" : "Rare Gem",
        "desc" : "A rare and valuable gemstone.",
        "price" : 200,
        "tier": 3
    },
    "missing homework" : {
        "name" : "Missing Homework",
        "desc" : "A piece of homework that was lost. It looks important.",
        "price" : 0,
        "tier": 1
    },
}

keys_dict = {
    "office key" : {
        "name" : "Office Key",
        "desc" : "A key that opens the principal's office door.",
        "price" : 0,
        "tier": 1
    },
    "principal key" : {
        "name" : "Principal's Key",
        "desc" : "A heavy brass key embossed with the school crest. It unlocks the principal's private office.",
        "price" : 0,
        "tier": 1
    },
}

# Combined lookup for all equippable items — maps item key -> info dict with "slot" added.
equipment_lookup = (
    {k: {**v, "slot": "body"}   for k, v in armor_dict.items()} |
    {k: {**v, "slot": "head"}   for k, v in helmets_dict.items()} |
    {k: {**v, "slot": "legs"}   for k, v in legs_dict.items()} |
    {k: {**v, "slot": "feet"}   for k, v in boots_dict.items()} |
    {k: {**v, "slot": "gloves"} for k, v in gloves_dict.items()} |
    {k: {**v, "slot": "tool"}   for k, v in tools_dict.items()}
    
)