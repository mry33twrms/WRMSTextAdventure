# armor

armor_dict = {
    
    "leather" : {
        "name" : "Leather Armor",
        "desc" : "Basic leather armor for protection.",
        "defense" : 4,
        "price" : 20,
    },

    "chainmail" : {
        "name" : "Chainmail Armor",
        "desc" : "A set of interlocking metal rings for protection.",
        "defense" : 7,
        "price" : 50
    },

    "plate" : {
        "name" : "Plate Armor",
        "desc" : "Heavy metal armor for maximum protection.",
        "defense" : 10,
        "price" : 100
    },

    "cloth" : {
        "name" : "Cloth Armor",
        "desc" : "Lightweight cloth armor for minimal protection.",
        "defense" : 2,
        "price" : 10
    },

    "cardboard" : {
        "name" : "Cardboard Armor",
        "desc" : "A makeshift armor made from cardboard. Not very effective.",
        "defense" : 1,
        "price" : 5
    },  
}

# boots

boots_dict = {
    
    "leather boots" : {
        "name" : "Leather Boots",
        "desc" : "Basic leather boots for protection.",
        "defense" : 2,
        "price" : 15
    },

    "steel boots" : {
        "name" : "Steel Boots",
        "desc" : "Heavy steel boots for maximum protection.",
        "defense" : 5,
        "price" : 40
    },

    "cloth shoes" : {
        "name" : "Cloth Shoes",
        "desc" : "Lightweight cloth shoes for minimal protection.",
        "defense" : 1,
        "price" : 5
    },

    "cardboard shoes" : {
        "name" : "Cardboard Shoes",
        "desc" : "A makeshift footwear made from cardboard. Not very effective.",
        "defense" : 0,
        "price" : 2
    },  
}

# gloves

gloves_dict = {
    
    "leather gloves" : {
        "name" : "Leather Gloves",
        "desc" : "Basic leather gloves for protection.",
        "defense" : 2,
        "price" : 10
    },

    "steel gauntlets" : {
        "name" : "Steel Gauntlets",
        "desc" : "Heavy steel gauntlets for maximum protection.",
        "defense" : 5,
        "price" : 30
    },

    "cloth gloves" : {
        "name" : "Cloth Gloves",
        "desc" : "Lightweight cloth gloves for minimal protection.",
        "defense" : 1,
        "price" : 5
    },

    "cardboard gloves" : {
        "name" : "Cardboard Gloves",
        "desc" : "A makeshift gloves made from cardboard. Not very effective.",
        "defense" : 0,
        "price" : 2
    },  
}

# helmets

helmets_dict = {
    
    "leather helmet" : {
        "name" : "Leather Helmet",
        "desc" : "Basic leather helmet for protection.",
        "defense" : 2,
        "price" : 15
    },

    "steel helmet" : {
        "name" : "Steel Helmet",
        "desc" : "Heavy steel helmet for maximum protection.",
        "defense" : 5,
        "price" : 40
    },

    "cloth hat" : {
        "name" : "Cloth Hat",
        "desc" : "Lightweight cloth hat for minimal protection.",
        "defense" : 1,
        "price" : 5
    },

    "cardboard hat" : {
        "name" : "Cardboard Hat",
        "desc" : "A makeshift hat made from cardboard. Not very effective.",
        "defense" : 0,
        "price" : 2
    },  
}

legs_dict = {
    
    "leather pants" : {
        "name" : "Leather Pants",
        "desc" : "Basic leather pants for protection.",
        "defense" : 2,
        "price" : 15
    },

    "steel greaves" : {
        "name" : "Steel Greaves",
        "desc" : "Heavy steel greaves for maximum protection.",
        "defense" : 5,
        "price" : 40
    },

    "cloth pants" : {
        "name" : "Cloth Pants",
        "desc" : "Lightweight cloth pants for minimal protection.",
        "defense" : 1,
        "price" : 5
    },

    "cardboard pants" : {
        "name" : "Cardboard Pants",
        "desc" : "A makeshift pants made from cardboard. Not very effective.",
        "defense" : 0,
        "price" : 2
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
        "price" : 5
    },

    "bread" : {
        "name" : "Bread",
        "desc" : "A loaf of bread that restores 10 HP.",
        "heal" : 10,
        "price" : 10
    },

    # recall scroll
    "recall scroll" : {
        "name" : "Recall Scroll",
        "desc" : "A scroll that allows you to teleport back to the starting area.",
        "price" : 50
    },
}

tools_dict = {
    "lockpick" : {
        "name" : "Lockpick",
        "desc" : "A small tool used to pick locks.",
        "price" : 10
    },
    "torch" : {
        "name" : "Torch",
        "desc" : "A wooden torch that can be used to light up dark areas.",
        "price" : 5
    },
    "rope" : {
        "name" : "Rope",
        "desc" : "A sturdy rope that can be used for climbing or tying things.",
        "price" : 15
    },
    "shovel" : {
        "name" : "Shovel",
        "desc" : "A tool used for digging.",
        "price" : 20
    },
    "pickaxe" : {
        "name" : "Pickaxe",
        "desc" : "A tool used for mining.",
        "price" : 25
    },
    "fishing rod" : {
        "name" : "Fishing Rod",
        "desc" : "A tool used for fishing.",
        "price" : 30
    },
}

# Combined lookup for all equippable items — maps item key -> info dict with "slot" added.
equipment_lookup = (
    {k: {**v, "slot": "body"} for k, v in armor_dict.items()} |
    {k: {**v, "slot": "head"} for k, v in helmets_dict.items()} |
    {k: {**v, "slot": "legs"} for k, v in legs_dict.items()} |
    {k: {**v, "slot": "feet"} for k, v in boots_dict.items()} |
    {k: {**v, "slot": "tool"} for k, v in tools_dict.items()}
)