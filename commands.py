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
    if direction.casefold() == "n" or direction == "North": return "north"
    elif direction.casefold() == "s" or direction == "South": return "south"
    elif direction.casefold() == "e" or direction == "East": return "east"
    elif direction.casefold() == "w" or direction == "West": return "west"
    elif direction.casefold() == "u" or direction == "Up": return "up"
    elif direction.casefold() == "d" or direction == "Down": return "down"
    else: return direction

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
    "north": {
        "func": lambda: print("You go north."),
        "desc": "Move north."
    },
    "south": {
        "func": lambda: print("You go south."),
        "desc": "Move south."
    },
    "east": {
        "func": lambda: print("You go east."),
        "desc": "Move east."
    },
    "west": {
        "func": lambda: print("You go west."),
        "desc": "Move west."
    },
    "up": {
        "func": lambda: print("You go up."),
        "desc": "Move up."
    },
    "down": {
        "func": lambda: print("You go down."),
        "desc": "Move down."
    },
}
