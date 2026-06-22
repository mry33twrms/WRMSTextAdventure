from rooms import room_dict
from npcs import npc_dict
import game_state

DIR_ALIASES = {
    "north": "n", "south": "s", "east": "e",
    "west": "w", "up": "u", "down": "d",
}

DIR_NAMES = {
    "n": "north", "s": "south", "e": "east",
    "w": "west", "u": "up", "d": "down",
}

OPPOSITE_DIR = {
    "n": "south", "s": "north", "e": "west",
    "w": "east", "u": "below", "d": "above",
}


async def broadcast_room(room_name, msg, exclude=None):
    for p in game_state.players.values():
        if p.current_room == room_name and p is not exclude:
            await p.send(msg)


async def display_room(room_name, player):
    room = room_dict[room_name]
    lines = [room["name"], "", room["desc"], ""]

    visible = []
    for npc_key in room.get("npcs", []):
        npc = npc_dict[npc_key]
        visible.append(f"- {npc['name']}: {npc['desc']}")
    for p in game_state.players.values():
        if p.current_room == room_name and p is not player:
            visible.append(f"- {p.name} is here.")

    if visible:
        lines.append("You see:")
        lines.extend(visible)
        lines.append("")

    exits = []
    for ex in room.get("exits", {}):
        if ex in DIR_NAMES:
            exits.append(DIR_NAMES[ex].capitalize())
        elif ex != "start":
            exits.append(ex)

    if exits:
        lines.append("Exits: " + ", ".join(exits))

    await player.send("\n".join(lines))


async def cmd_look(player, args, gs):
    if not args:
        await display_room(player.current_room, player)
        return
    target = args.casefold()
    for npc_key in room_dict[player.current_room].get("npcs", []):
        if target in npc_key.casefold() or target in npc_dict[npc_key]["name"].casefold():
            await player.send(npc_dict[npc_key]["desc"])
            return
    for p in gs.players.values():
        if p.current_room == player.current_room and target in p.name.casefold():
            await player.send(f"{p.name} is a player adventuring through WRMS.")
            return
    await player.send(f"You don't see '{args}' here.")


async def cmd_quit(player, _args, _gs):
    await player.send("Goodbye!")
    player.quitting = True


async def cmd_help(player, _args, _gs):
    lines = [f"{key} - {info['desc']}" for key, info in commands_dict.items()]
    await player.send("\n".join(lines))


async def cmd_start(player, _args, gs):
    await cmd_move(player, "start", gs)


async def cmd_say(player, args, _gs):
    if not args:
        await player.send("Say what?")
        return
    await player.send(f'You say: "{args}"')
    await broadcast_room(player.current_room, f'{player.name} says: "{args}"', exclude=player)


async def cmd_list_rooms(player, args, gs):
    lines = ["Rooms:"] + [f"  {key} - {room['name']}" for key, room in room_dict.items()]
    await player.send("\n".join(lines))


async def cmd_change_room(player, args, gs):
    if not args:
        await player.send("Usage: change room <room name>")
        return
    if args not in room_dict:
        await player.send(f"Room '{args}' not found.")
        return
    old_room = player.current_room
    await broadcast_room(old_room, f"{player.name} vanishes into thin air.", exclude=player)
    player.current_room = args
    await broadcast_room(args, f"{player.name} appears out of thin air.", exclude=player)
    await display_room(args, player)


async def cmd_bonk(player, args, gs):
    if not args:
        await player.send("Usage: bonk <mob name>")
        return
    mobs = room_dict[player.current_room].get("mobs", [])
    if args in mobs:
        mobs.remove(args)
        await player.send(f"You bonk the {args} on the head. It wanders off confused.")
        await broadcast_room(player.current_room, f"{player.name} bonks the {args} on the head!", exclude=player)
    else:
        await player.send(f"There is no '{args}' here to bonk.")


async def cmd_who(player, args, gs):
    if not gs.players:
        await player.send("No one is connected.")
        return
    lines = ["Players online:"]
    for p in gs.players.values():
        marker = " (you)" if p is player else ""
        lines.append(f"  {p.name} - {room_dict[p.current_room]['name']}{marker}")
    await player.send("\n".join(lines))


async def cmd_move(player, direction, gs):
    room = room_dict[player.current_room]
    exits = room.get("exits", {})
    if direction not in exits:
        await player.send("You can't go that way.")
        return

    new_room_key = exits[direction]
    if new_room_key not in room_dict:
        await player.send("That passage leads nowhere. (Missing room)")
        return

    old_room = player.current_room

    if direction in DIR_NAMES:
        await broadcast_room(old_room, f"{player.name} leaves to the {DIR_NAMES[direction]}.", exclude=player)
        await broadcast_room(new_room_key, f"{player.name} arrives from the {OPPOSITE_DIR[direction]}.", exclude=player)

    player.current_room = new_room_key
    await display_room(new_room_key, player)


commands_dict = {
    "quit":        {"func": cmd_quit,        "desc": "Disconnect from the MUD."},
    "help":        {"func": cmd_help,        "desc": "List all commands."},
    "look":        {"func": cmd_look,        "desc": "Look at the room, or 'look <name>' to examine someone."},
    "say":         {"func": cmd_say,         "desc": "Say something to everyone in the room."},
    "who":         {"func": cmd_who,         "desc": "List all connected players."},
    "start":       {"func": cmd_start,       "desc": "Start the game from the main menu."},
    "list rooms":  {"func": cmd_list_rooms,  "desc": "List all rooms in the game."},
    "change room": {"func": cmd_change_room, "desc": "Teleport to a room: change room <name>"},
    "bonk":        {"func": cmd_bonk,        "desc": "Bonk a mob: bonk <mob name>"},
    "n":  {"func": lambda p, a, gs: cmd_move(p, "n", gs),  "desc": "Move north."},
    "s":  {"func": lambda p, a, gs: cmd_move(p, "s", gs),  "desc": "Move south."},
    "e":  {"func": lambda p, a, gs: cmd_move(p, "e", gs),  "desc": "Move east."},
    "w":  {"func": lambda p, a, gs: cmd_move(p, "w", gs),  "desc": "Move west."},
    "u":  {"func": lambda p, a, gs: cmd_move(p, "u", gs),  "desc": "Move up."},
    "d":  {"func": lambda p, a, gs: cmd_move(p, "d", gs),  "desc": "Move down."},
}


async def handle_command(raw_input, player, gs):
    text = raw_input.strip()
    if not text:
        return

    lower = text.casefold()

    # Resolve direction aliases (north -> n, etc.)
    first_word = lower.split()[0]
    if first_word in DIR_ALIASES:
        lower = DIR_ALIASES[first_word]

    # Longest prefix match against commands_dict
    best_key = None
    best_args = ""
    for cmd_key in commands_dict:
        if lower == cmd_key:
            if best_key is None or len(cmd_key) >= len(best_key):
                best_key = cmd_key
                best_args = ""
        elif lower.startswith(cmd_key + " "):
            if best_key is None or len(cmd_key) > len(best_key):
                best_key = cmd_key
                best_args = lower[len(cmd_key):].strip()

    if best_key is not None:
        await commands_dict[best_key]["func"](player, best_args, gs)
        return

    await player.send("Invalid input. Type 'help' for a command list.")
