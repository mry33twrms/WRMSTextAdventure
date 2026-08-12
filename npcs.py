npc_dict = {
    
    "Goose": {
        "name": "Goostopher",
        "desc": "A large, aggressive goose. It looks like it has been here for a while.",
    },

    "Kristi": {
        "name": "Kristi",
        "desc": "A friendly receptionist. She seems to be busy with her work.",
    },
    
    'Miss Cass': {
        'name':'Miss Cass',
        'desc':'She is working behind the counter selling students all the snacks and drinks they want.',
        'shop': {
            'sell_dict': {
                "apple": 5, "bread": 3, "health potion": 10,
                "lockpick": 15, "torch": 8, "rope": 12,
                "shovel": 20, "pickaxe": 25, "fishing rod": 18,
            },
            'buy_dict': {
                "apple": 2, "bread": 2, "health potion": 5,
                "lockpick": 10, "rope": 6, "shovel": 10,
                "pickaxe": 15, "fishing rod": 9,
            },
        },
        'convos' : {
            'greeting' : "Hello there! Welcome to Campus Corner. Say 'buy' to see what's for sale, or 'sell' to sell me something.",
            'farewell' : "Thanks for stopping by! Have a great day!",
            'default' : "I'm not sure what you mean. Say 'buy' or 'sell' to trade, or say goodbye when you're done.",
            'dog' : "Oh, you have a dog! That's so cute! I love dogs.",
            'cat' : "Oh, you have a cat! That's so cute! I love cats.",
        },
    },
    
    'Miss Crestwell':{
        'name':'Miss Crestwell',
        'desc':'She is sitting at a small table excitedly trying to sell ceramic poppies.',
        'convos' : {
            'greeting' : "Hello there! Welcome to the Ceramic Shop. What can I get for you today?",
            'farewell' : "Thanks for stopping by! Have a great day!",
            'default' : "I'm sorry, I don't understand. Can you please rephrase that?",
        },
    }
    
}