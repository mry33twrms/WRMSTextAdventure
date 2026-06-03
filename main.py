from rooms import room_dict
from npcs import npc_dict
from commands import * # This means to import all functions and variables.
import sys

game_running = True
current_room = "front admin"

while game_running:

    displayRoom(current_room)
    response = input(">> ")
    

    if dir_check(response) in commands_dict.keys():
        commands_dict[dir_check(response)]["func"]()
    else:
        print("Invalid input. Type 'help' for command list.")

