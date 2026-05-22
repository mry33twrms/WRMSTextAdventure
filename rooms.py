room_dict = {

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
            "s" : "front admin"
            },
        "npcs" : ["Goose"]
    }

}