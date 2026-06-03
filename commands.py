from rooms import room_dict
from npcs import npc_dict
import sys

def displayRoom(room_name):
    print(room_dict[room_name]["name"])
    print()
    print(room_dict[room_name]["desc"])
    print()

    exit_list = []
    for exit in room_dict[room_name]["exits"].keys():
        if exit == "n": exit_list.append("North")
        elif exit == "s": exit_list.append("South")
        elif exit == "e": exit_list.append("East")
        elif exit == "w": exit_list.append("West")
        elif exit == "u": exit_list.append("Up")
        elif exit == "d": exit_list.append("Down")
        else: exit_list.append(exit)
    
    print(", ".join(exit_list))

def look(target, room_name):
    for t in room_dict[room_name]["npcs"]:
        if target == t:
            return npc_dict[t]["desc"]

def help():
    for command in commands_dict.keys():
        print(f"{command} - {commands_dict[command]['desc']}")

def change_room():
    global current_room
    new_room = input("Enter room name: ")
    if new_room in room_dict.keys():
        current_room = new_room
    else:
        print("Invalid room name.")

# Direction Check - allows for multiple inputs for the same direction. 
# For example, "n" and "North" will both be recognized as north. 
# This is used in the movement commands to allow for more flexible input.
# If the argument entered it is not a direction it will return the original argument.

def dir_check(direction): 
    if direction.casefold() == "n" or direction == "north": return "n"
    elif direction.casefold() == "s" or direction == "south": return "s"
    elif direction.casefold() == "e" or direction == "east": return "e"
    elif direction.casefold() == "w" or direction == "west": return "w"
    elif direction.casefold() == "u" or direction == "up": return "u"
    elif direction.casefold() == "d" or direction == "down": return "d"
    else: return direction

def move_player(direction):
    global current_room
    if direction in room_dict[current_room]["exits"].keys():
        current_room = room_dict[current_room]["exits"][direction]
        print(f"You go {direction}.")
    else:
        print("You can't go that way.")

commands_dict = {
    "quit": {
        "func": lambda: sys.exit(),
        "desc": "Quit the program."     
    },
    "help": {
        "func": help,
        "desc": "Lists all commands and their descriptions."
    },
    "change room": {
        "func": change_room,
        "desc": "Change the current room."
    },
    "n": {
        "func": lambda: move_player("n"),
        "desc": "Move north."
    },
    "s": {
        "func": lambda: move_player("s"),
        "desc": "Move south."
    },
    "e": {
        "func": lambda: move_player("e"),
        "desc": "Move east."
    },
    "w": {
        "func": lambda: move_player("w"),
        "desc": "Move west."
    },
    "u": {
        "func": lambda: move_player("u"),
        "desc": "Move up."
    },
    "d": {
        "func": lambda: move_player("d"),
        "desc": "Move down."
    },
}
