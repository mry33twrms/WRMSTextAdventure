from rooms import roomdict

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



while game_running:
    
    displayRoom("driveway")

    game_running = False

