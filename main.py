from rooms import room_dict
from npcs import npc_dict
import sys

game_running = True
current_room = "front admin"

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
    }
}



while game_running:

    response = input(">> ")
    
    if response in commands_dict.keys():
        commands_dict[response]["func"]()
    else:
        print("Invalid input. Type 'help' for command list.")

    displayRoom(current_room)