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

    current_room = player.current_room

    if direction in room_dict[current_room]["exits"]:

        new_room = room_dict[current_room]["exits"][direction]

        print(f"You go {direction}.")

        player.current_room = new_room

    else:
        print("You can't go that way.")


commands_dict = {

    "quit": {
        "func": lambda player: sys.exit(),
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