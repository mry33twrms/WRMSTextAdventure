from rooms import roomdict
from npcs import npcDict

game_running = True

def displayRoom(room_name):
    print(roomdict[room_name]["name"])
    print()
    print(roomdict[room_name]["desc"])
    print()

    exit_list = []
    for exit in roomdict[room_name]["exits"].keys():
        if exit == "n": exit_list.append("North")
        elif exit == "s": exit_list.append("South")
        elif exit == "e": exit_list.append("East")
        elif exit == "w": exit_list.append("West")
        elif exit == "u": exit_list.append("Up")
        elif exit == "d": exit_list.append("Down")
        else: exit_list.append(exit)
    
    print(", ".join(exit_list))

def look(target, room_name):
    for t in roomdict[room_name]["npcs"]:
        if target == t:
            return npcDict[t]["desc"]

    


while game_running:
    
    displayRoom("driveway")

    game_running = False

