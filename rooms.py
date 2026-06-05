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
            "n" : "driveway",
            "s" : "back admin"
            },
        "npcs" : ["Kristi"]
    },

    "driveway" : {
        "name" : "Front Administration Driveway",
        "desc" : "A gosse sits in a an oversized planter box. It hisses at you and you feel like you shouldn't be there.",
        "exits" : {
            "s" : "front admin",
            "portal": "bus hall"},
        "npcs" : ["Goose"],
        "mobs" : ["orc guard"]
    },
    
    'back admin' : {
        'name' : 'Back Administration',
        'desc' : 'An empty room with two hallways going to the left and right of you one leads to the student centre, gym, and classsrooms, while the other leads to the bus hall and cafeteria. There is also a large window with two sets of doors going out into the courtyard.',
        'npcs' : ['Miss Crestwell'],
        'exits' : {
            'n':'courtyard',
            'w':'gym hallway',
            'e':'bus hall',
        },
    },
    
    'bus hall':{
        'name' : 'Bus Hall',
        'desc' : 'A hallway to the cafeteria filled with suitcases and bags from all the students, there is a door at the end of the hallway to the cafeteria.',
        'exits' : {
            's':'cafeteria',
            'w':'back admin',
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
        'npcs' : []
    },

    'campus corner':{
        'name':'Campus Corner',
        'desc':'A small store selling all sorts of snacks and drinks. Miss Cass works behind the counter',
        'exits':{
            'e':'student centre',
        },
        'npcs' : []
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

    "auditorium" : {
        "name" : "auditorium",
        "desc" : "large area that slowly goes down hill containing a grand piano, several movie theatre style chairs, a cane trap, and much more.",
        "exits" : {
            "s" : "life skills"
            },
        'npcs' : []
    },

    "life skills" : {
        "name" : "life skills room",
        "desc" : "a kitchen style room.",
        "exits" : {
            "s" : "park place"
            },
        'npcs' : [] 
    },

    "park place" : {
        "name" : "park place residence",
        "desc" : "an apartment building style unit.",
        "exits" : {
            "s" : "student health",
            },
        'npcs' : []
    },
      
    "student health" : {
        "name" : "student health",
        "desc" : "a busy room with smaller rooms inside it.",
        "exits" : {
            "s" : "rock garden",
            "n" : "park place"
            },
        'npcs' : []
    },

    "midi lab" : {
        "name" : "midi lab",
        "desc" : "a room filled with tables, chairs, computers, and pianos.",
        "exits" : {
            "s" : "live room",
            "n" : "recording studio",
            "w" : "practice room 12"
            },
        'npcs' : []
    },

    "recording studio" : {
        "name" : "recording studio",
        "desc" : "this is where all the music production happens.",
        "exits" : {
            "s" : "live room",
            "n" : "instrument room",
            "w" : "practice room 12"
            },
        'npcs' : []
    },

    "recording studio" : {
        "name" : "recording studio",
        "desc" : "this is where all the music production happens.",
        "exits" : {
            "s" : "live room",
            "n" : "instrument room",
            "w" : "practice room 12"
            },
        'npcs' : []
    },
    "live room" : {
        "name" : "live room",
        "desc" : "second room where all the music production happens.",
        "exits" : {
            "s" : "piano studio",
            "n" : "instrument room",
            "w" : "back of auditorium",
            },
        'npcs' : []
    },
    "instrument room" : {
        "name" : "instrument room",
        "desc" : "small room where all the instruments live.",
        "exits" : {
            "s" : "piano studio",
            "n" : "court yard",
            "w" : "back of auditorium",
            },
        'npcs' : []
    },

    'classroom hallway':{
        'name':'Classroom hallway',
        'desc':'A long hallway with classrooms on either side, the choral room, and a shortcut to the elementary area at the end of the hall, and a staircase up to the highschool classes and down to the deaf blind classes.',
        'exits':{
            'n':'elementary shortcut',
            'w':'choral room',
            's':'gym hallway',
            'u':'highschool classes',
            'd':'db classes',
        },
    },
    'choral room':{
        'name':'Choral Room',
        'desc':'A room filled with instruments and mismatched chairs in a circle.',
        'exits':{
            'e':'classroom hallway',
        },
    },
    'gym entrance':{
        'name':'Gym Entracne',
        'desc':'the entrance to the gym, the music wing is on one side and the hallway to the senior lodging entrance is on the other.',
        'exits':{
            'w':'gym',
            'n':'senior intersection',
            's':'music wing',
        },
    },
    'senior intersection':{
        'name':'Senior Intersection',
        'desc':'The intersection between Senior Lodging and the classrooom hallway.',
        'exits':{
            'w':'senior residence',
            'e':'classroom hallway',
        },
    },
    'senior basement':{
        'name':'Senior Lodging Basement',
        'desc':'A creppy basement made entirally of concrete, it definitly looks haunted or at least like rats live down there.',
        'exits':{
            'u':'senior residence',
            's':'decoration room',
        },
    },
    'decoration room':{
        'name':'Decorations Room',
        'desc':"A room full of Halloween and Christmas decorations, its super dusty and looks like a mess of holidays that hasn't been organised in decades.",
        'exits':{
            'n':'senior basement',
        },
    },
    'gym':{
        'name':'Gym',
        'desc':"It's a very large room with a goalball court on one side and wrestling mats on the other.",
        'npcs':['Miss Howe'],
        'exits':{
            'e':'gym intersection',
            'w':'pool'
        },
    },
    'db classes':{
        'name':'Main School Basement',
        'desc':'A hallway that looks very similar to the one above it, theres the cooking classroom and an intersection behind you leading to more classes.',
        'exits':{
            'w':'cooking class',
            's':'basement intersection',
        },
    },
    'cooking class':{
        'name':'Cooking Class',
        'desc':'A room with three different kitchens in it filled with lots of cooking supplies, it smells vaugly like cookies.',
        'npcs':['Mr Howe'],
        'exits':{
            'e':'db classes',
        },
    },
    

}
