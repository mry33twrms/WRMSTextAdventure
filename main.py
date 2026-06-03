import commands
from commands import *
from player import Player
import sys

game_running = True

player1 = Player("Player", "front admin")

while game_running:

    displayRoom(player1.current_room)

    response = input(">> ")
    response = response.casefold()

    command = dir_check(response)

    if command in commands_dict:
        commands_dict[command]["func"](player1)
    else:
        print("Invalid input. Type 'help' for command list.")