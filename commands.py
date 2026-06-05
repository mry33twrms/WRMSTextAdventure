from rooms import room_dict
from npcs import npc_dict
import sys

def quit(player=None):
    sys.exit()

def displayRoom(room_name):
    print(room_dict[room_name]["name"])
    print()
    print(room_dict[room_name]["desc"])
    print()
    if room_dict[room_name]["npcs"]:
        print("You see:")
        for npc in room_dict[room_name]["npcs"]:
            print(f"- {npc_dict[npc]['name']}:\n{npc_dict[npc]['desc']}")
        print()

    exit_list = []

    for exit in room_dict[room_name]["exits"].keys():
        if exit == "n":
            exit_list.append("North")
        elif exit == "s":
            exit_list.append("South")
        elif exit == "e":
            exit_list.append("East")
        elif exit == "w":
            exit_list.append("West")
        elif exit == "u":
            exit_list.append("Up")
        elif exit == "d":
            exit_list.append("Down")
        elif exit == "start":
            exit_list.append("")
        else:
            exit_list.append(exit)

    print(", ".join(exit_list))


def look(target, room_name):
    for t in room_dict[room_name]["npcs"]:
        if target == t:
            return npc_dict[t]["desc"]


def help(player=None):
    for command in commands_dict.keys():
        print(f"{command} - {commands_dict[command]['desc']}")


def change_room(player):
    new_room = input("Enter room name: ")

    if new_room in room_dict:
        player.current_room = new_room
    else:
        print("Invalid room name.")


def dir_check(direction):

    direction = direction.casefold()

    if direction == "n" or direction == "north":
        return "n"
    elif direction == "s" or direction == "south":
        return "s"
    elif direction == "e" or direction == "east":
        return "e"
    elif direction == "w" or direction == "west":
        return "w"
    elif direction == "u" or direction == "up":
        return "u"
    elif direction == "d" or direction == "down":
        return "d"
    else:
        return direction

def move_player(direction, player):

    dirlist = ["n", "s", "e", "w", "u", "d"]

    current_room = player.current_room

    if direction in room_dict[current_room]["exits"]:

        new_room = room_dict[current_room]["exits"][direction]
        
        if direction in dirlist:
            print(f"You go {direction}.")
        
        player.current_room = new_room

    else:
        print("You can't go that way.")

def bonk(player, mob):
    if mob in room_dict[player.current_room]["mobs"]:
        print(f"You bonk the {mob} on the head. It looks at you confusedly.")
        room_dict[player.current_room]["mobs"].remove(mob)
        del room_dict[player.current_room]["mobs"][mob]
    else:
        print(f"There is no {mob} here to bonk.")

commands_dict = {

    "quit": {
        "func": quit,
        "desc": "Quit the program."
    },

    "help": {
        "func": help,
        "desc": "Lists all commands and their descriptions."
    },
    
    "start": {
        "func": lambda player: move_player("start", player),
        "desc": "Start the game from the main menu."
    },

    "change room": {
        "func": change_room,
        "desc": "Change the current room."
    },
    
    "bonk": {
        "func": lambda player: bonk(player, input("Enter mob name: ")),
        "desc": "Bonk a mob on the head to remove it from the room."
    },

    "n": {
        "func": lambda player: move_player("n", player),
        "desc": "Move north."
    },

    "s": {
        "func": lambda player: move_player("s", player),
        "desc": "Move south."
    },

    "e": {
        "func": lambda player: move_player("e", player),
        "desc": "Move east."
    },

    "w": {
        "func": lambda player: move_player("w", player),
        "desc": "Move west."
    },

    "u": {
        "func": lambda player: move_player("u", player),
        "desc": "Move up."
    },

    "d": {
        "func": lambda player: move_player("d", player),
        "desc": "Move down."
    },
    
}