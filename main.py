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

command_dict = {
    "quit" : sys.exit(),
}


while game_running:
    
    displayRoom(current_room)

    response = input(">> ")
    
    if response in command_dict.keys():
        command_dict[response]
#    elif response in roomdict[current_room]["exits"].keys():
#       current_room = roomdict[current_room]["exits"][response]
    else:
        print("Invalid command.")

        


