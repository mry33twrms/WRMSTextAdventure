'''

Rooms and their properties are defined here. Each room is a dictionary with the following keys:
- "name": The name of the room.
- "desc": A description of the room.
- "exits": A dictionary mapping exit names to the keys of the rooms they lead to. Use Cardinal directions (n, s, e, w, u, d) for standard exits. Use any other string for special exits.
- "npcs": A list of NPC names present in the room.
- "items": A list of item names present in the room (optional).
- "mobs": A list of mob names present in the room (optional).
- "features" : A list of special features in the room such as fishing holes and ores to mine  (optional).
- "shop" : A boolean indicating if the room is a shop and a list of items that can be bought and sold in the room (optional).
- "guarded" : A list of exits that are guarded by mobs(optional).
- "hostile" : A boolean indicating if the mobs in the room are hostile to the player (optional).
- "locked" : A list with a boolean indicating if the room is locked and requires a key to enter and a string of the name of the item/key needed to open. (optional).
- "states" : A list of states that the room can be in such as on fire or full of smoke. Each state is a dictionary with the following keys:
    - "name": The name of the state.
    - "desc": A description of the room in that state.
    - "modifiers": A dictionary of modifiers that affect the room's properties in that state (optional).

'''

room_dict = {

    "menu" : {
        "name" : "Main Menu",
        "desc" : "Welcome to the WRMS Text Adventure!\nType 'Start' to continue\n\nType 'help' for command list",
        "exits" : {'start' : 'front admin'},
        "npcs" : []
    },

    "front admin" : {
        "name" : "Front Administration Lobby",
        "desc" : "A large open room with brick walls, a skylight, and a reception desk.",
        "exits" : {
            "s" : "driveway",
            "n" : "back admin"
            },
        "npcs" : ["Kristi"],
        "items" : ["leather", "short sword", "health potion"],
        "features" : ["respawn point"],
    },

    "driveway" : {
        "name" : "Front Administration Driveway",
        "desc" : "A gosse sits in a an oversized planter box. It hisses at you and you feel like you shouldn't be there.",
        "exits" : {
            "n" : "front admin",
            "portal": "bus hall"},
        "npcs" : ["Goose"],
        "mobs" : ["goblin"],
        "features" : ["fishing hole"],
    },
    
    'back admin' : {
        'name' : 'Back Administration',
        'desc' : 'An empty room with two hallways going to the left and right of you one leads to the student centre, gym, and classsrooms, while the other leads to the bus hall and cafeteria. There is also a large window with two sets of doors going out into the courtyard.',
        'npcs' : ['Miss Crestwell'],
        'exits' : {
            'n':'courtyard',
            's':'front admin',
            'w':'gym hallway',
            'e':'bus hall',
        },
    },
    
    'bus hall':{
        'name' : 'Bus Hall',
        'desc' : 'A hallway to the cafeteria filled with suitcases and bags from all the students, there is a door at the end of the hallway to the cafeteria.',
        'exits' : {
            'n':'cafeteria',
            'w':'back admin',
            # 'e':'Bus Parking Lot',  # This exit is commented out, possibly for future use
        },
        'npcs' : []
    },

    'gym hallway':{
        'name':'Gym Hallway',
        'desc':'A hallway leading to the gym at the end of the hall and the Student Centre on one side and hallways leading to classrooms on the other, the music wing hallway is also next to the gym farther down the hall.',
        'exits':{
            'n':'classroom hallway',
            'w':'gym entrance',
            's':'student centre',
            'e':'back admin',
        },
        'npcs' : []
    },

    'student centre':{
        'name':'Student Centre',
        'desc':'A large room filled with tables and chairs to sit and couches, its full of students hanging out or doing homework. Campus Corner is to the right and there is an exit to the music wing in the back of the Student Centre.',
        'exits':{
            'w':'campus corner',
            's':'music wing',
            'n':'gym hallway',
        },
        'npcs' : [],

    },

    'campus corner':{
        'name':'Campus Corner',
        'desc':'A small store selling all sorts of snacks and drinks. Miss Cass works behind the counter',
        'exits':{
            'e':'student centre',
            },
        'npcs' : ['Miss Cass'],
    },
    
    "o and m room" : {
        "name" : "O and M room",
        "desc" : "A large room with a cane holder containing lots of different sized white canes on the right side of the room enterance.",
        "exits" : {
            "e" : "cafeteria"
            },
        'npcs' : []
    },
    
    "cafeteria" : {
        "name" : "cafeteria",
        "desc" : "a very large, rectangular shaped room filled with lots of chairs and tables in the center of the room.",
        "exits" : {
            "s" : "bus hall",
            "w" : "o and m room"
            },
        'npcs' : []
    },
    
    "brant place" : {
        "name" : "Brant Place",
        "desc" : "wood chips and swings can be found along side benches and picnic tables and grass.",
        "exits" : {
            "s" : "senior residence"
            },
        'npcs' : []
    },
    
    "senior residence" : {
        "name" : "senior lodge",
        "desc" : "Concrete building with 3 levels of apartment style areas.",
        "exits" : {
            "s" : "junior residence"
            },
        'npcs' : []
    },
    
    "junior residence" : {
       "name" : "Neil lodge",
       "desc" : "Similar to seinior lodge but for junior students. There is only 1 floor, not 3.",
       "exits" : {
           "s" : "activity room"
        },
        'npcs' : []
    },

    "activity room" : {
        "name" : "activity room",
        "desc" : "a room with crafts and games.",
        "exits" : {
            "s" : "music wing"
        },
        'npcs' : []
    },
    
    "music wing" : {
        "name" : "music wing",
        "desc" : "a long hall way with a piano studio, practice rooms, and music production rooms surounding the hall way.",
        "exits" : {
            "s" : "auditoriom"
        },
        'npcs' : []
    },

}
