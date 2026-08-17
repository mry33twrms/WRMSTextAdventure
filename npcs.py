npc_dict = {
    
    "Goose": {
        "name": "Goostopher",
        "desc": "A large, aggressive goose. It looks like it has been here for a while.",
    },

    "Kristi": {
        "name": "Kristi",
        "desc": "A friendly receptionist. She seems to be busy with her work.",
        "convos": {
            "greeting": "Hello there! Welcome to the school! I can help you out or give you a quest if you need one.",
            "farewell": "Thanks for stopping by! Have a great day!",
            "default":  "I'm not sure what you mean. Can you please rephrase that?",
            "help": {
                "text":     "Here's a health potion — it'll restore some HP. Stay safe out there!",
                "action":   "give_item",
                "item_key": "health potion",
                "once":     True,
                "once_msg": "Sorry, I'm all out of potions!",
            },
            "quest": {
                "text":              "I need your help! The homework I was grading has gone missing. Rumour has it the bell in the courtyard has something to do with it. Try ringing it.",
                "action":            "give_quest",
                "quest_id":          "missing_homework",
                "quest_name":        "Missing Homework",
                "quest_desc":        "Find the missing homework in the courtyard by ringing the bell, then say 'homework' to Kristi to claim your reward.",
                "already_given_msg": "Still looking for that homework? Try ringing the bell in the courtyard!",
            },
            "homework": {
                "text":                "You found it! Oh thank you so much — here, take this apple as a reward.",
                "action":              "complete_quest",
                "quest_id":            "missing_homework",
                "requires_quest_item": "missing homework",
                "reward_item":         "apple",
                "no_quest_msg":        "Homework? I haven't asked you about any homework yet.",
                "no_item_msg":         "You haven't found the homework yet. Try ringing the bell in the courtyard!",
            },
        },
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
    },

    'Cindi': {
        'name': 'Cindi',
        'desc': 'An administrative assistant surrounded by stacks of paperwork. She looks very busy.',
        'convos': {
            'greeting': "Hello! I'm very busy right now. Is there something I can help you with?",
            'farewell': "Have a good day!",
            'default':  "Sorry, I really can't chat right now. Too much to do!",
        },
    },

}