import asyncio
import json
from player import Player
import game_state
import database as db
from commands import handle_command, display_room, _hostile_check_loop, _party_leave_cleanup, _follow_cleanup
from rooms import room_dict
from config import PWD_SIGNAL

VERSION = "0.20"
HOST = "0.0.0.0"
PORT = 4000

LOGIN_TIMEOUT = 60   # seconds per login prompt before disconnect
MAX_AUTH_TRIES = 3   # wrong-password attempts before disconnect


async def _send(writer, msg):
    writer.write((msg + "\n").encode())
    await writer.drain()


async def _prompt(reader, writer, prompt, timeout=LOGIN_TIMEOUT, password=False):
    """Write prompt, return stripped response or None on timeout/disconnect.

    Pass password=True to tell the client to mask input with stars.
    """
    prefix = PWD_SIGNAL if password else ""
    writer.write((prefix + prompt).encode())
    await writer.drain()
    try:
        line = await asyncio.wait_for(reader.readline(), timeout=timeout)
    except asyncio.TimeoutError:
        await _send(writer, "Timed out.")
        return None
    if not line:
        return None
    return line.decode(errors="replace").strip()


def _load_player_from_db(player, data):
    """Overwrite a freshly-created Player with saved DB values."""
    player.gold              = data["gold"]
    player.inventory         = json.loads(data["inventory"])
    _DEFAULT_SLOTS = {
        "head": None, "body": None, "legs": None, "feet": None,
        "gloves": None, "weapon": None, "shield": None,
        "accessory": None, "tool": None,
    }
    player.equipped_items = {**_DEFAULT_SLOTS, **json.loads(data["equipped_items"])}
    player.strength          = data["strength"]
    player.agility           = data["agility"]
    player.intelligence      = data["intelligence"]
    player.vitality          = data["vitality"]
    player.level             = data["level"]
    player.xp                = data["xp"]
    player.stat_points       = data["stat_points"]
    player.bonus_attack      = data["bonus_attack"]
    player.bonus_defense     = data["bonus_defense"]
    player.respawn_point     = data["respawn_point"]
    player.quests            = json.loads(data["quests"])
    player.quest_items       = json.loads(data["quest_items"])
    player.received_npc_items = set(json.loads(data["received_npc_items"]))
    player.concise_mode  = bool(data.get("concise_mode", 0))
    player.visited_rooms = set(json.loads(data.get("visited_rooms", "[]")))
    # Normalize legacy saves: equipped items must not also sit in inventory
    for key in player.equipped_items.values():
        if key and key in player.inventory:
            player.inventory.remove(key)

    player.recalculate_stats()
    saved_hp = data["hp"]
    saved_mp = data["mp"]
    player.hp = min(saved_hp, player.max_hp) if saved_hp > 0 else player.max_hp
    player.mp = min(saved_mp, player.max_mp) if saved_mp > 0 else player.max_mp
    saved_room = data["current_room"]
    player.current_room = saved_room if saved_room in room_dict else "front admin"


async def _first_run_setup(reader, writer):
    """Interactive setup for the very first admin account. Returns (name, role, data) or None."""
    await _send(writer, "")
    await _send(writer, "=== WRMS MUD — First Run Setup ===")
    await _send(writer, "No admin account found. Please create one now.")
    await _send(writer, "")

    name = await _prompt(reader, writer, "Admin username: ")
    if not name:
        return None

    while True:
        pw = await _prompt(reader, writer, "Admin password: ", password=True)
        if pw is None:
            return None
        confirm = await _prompt(reader, writer, "Confirm password: ", password=True)
        if confirm is None:
            return None
        if pw != confirm:
            await _send(writer, "Passwords do not match. Try again.")
            continue
        if len(pw) < 4:
            await _send(writer, "Password must be at least 4 characters.")
            continue
        break

    email = await _prompt(reader, writer, "Admin email (optional — press Enter to skip): ")
    if email is None:
        email = ""

    db.create_account(name, pw, email, role="admin")
    await _send(writer, f"\nAdmin account '{name}' created.")
    db.update_last_login(name)
    return name, "admin", db.load_player_data(name)


async def _login_flow(reader, writer):
    """
    Handle login or account creation.
    Returns (name, role, data_dict) on success, or None on failure/disconnect.
    """
    await _send(writer, "")

    account_name = await _prompt(reader, writer, "Account name: ")
    if not account_name:
        return None

    canonical = db.get_canonical_name(account_name)

    if canonical:
        # ── Existing account ──────────────────────────────────────────
        for attempt in range(1, MAX_AUTH_TRIES + 1):
            pw = await _prompt(reader, writer, "Password: ", password=True)
            if pw is None:
                return None
            if db.verify_password(canonical, pw):
                break
            remaining = MAX_AUTH_TRIES - attempt
            if remaining:
                await _send(writer, f"Incorrect password. {remaining} attempt(s) remaining.")
            else:
                await _send(writer, "Too many failed attempts. Goodbye.")
                return None

        # Check for already-connected duplicate
        if canonical in game_state.players:
            await _send(writer, f"'{canonical}' is already logged in.")
            return None

        db.update_last_login(canonical)
        role = db.get_role(canonical)
        data = db.load_player_data(canonical)
        await _send(writer, f"Welcome back, {canonical}!")
        return canonical, role, data

    else:
        # ── New account ───────────────────────────────────────────────
        await _send(writer, f"No account named '{account_name}' found. Creating a new account.")
        await _send(writer, "")

        while True:
            pw = await _prompt(reader, writer, "Create password: ", password=True)
            if pw is None:
                return None
            if len(pw) < 4:
                await _send(writer, "Password must be at least 4 characters.")
                continue
            confirm = await _prompt(reader, writer, "Confirm password: ", password=True)
            if confirm is None:
                return None
            if pw != confirm:
                await _send(writer, "Passwords do not match. Try again.")
                continue
            break

        email = await _prompt(reader, writer, "Email address (optional — press Enter to skip): ")
        if email is None:
            email = ""

        db.create_account(account_name, pw, email, role="player")
        await _send(writer, f"\nAccount '{account_name}' created. Welcome to WRMS MUD!")
        db.update_last_login(account_name)
        data = db.load_player_data(account_name)
        return account_name, "player", data


async def handle_client(reader, writer):
    addr = writer.get_extra_info("peername")
    print(f"Connection from {addr}")
    name = None

    try:
        await _send(writer, f"WRMS MUD v{VERSION}")

        # First-run: no admins exist yet
        if not db.has_any_admin():
            result = await _first_run_setup(reader, writer)
        else:
            result = await _login_flow(reader, writer)

        if result is None:
            return

        name, role, player_data = result

        # Build player and restore saved state
        player = Player(name, "front admin", writer)
        player.role = role
        _load_player_from_db(player, player_data)

        game_state.players[name] = player

        role_label = " [Admin]" if role == "admin" else ""
        for p in game_state.players.values():
            if p is not player:
                await p.send(f"*** {name}{role_label} has entered the MUD. ***")

        await display_room(player.current_room, player)

        try:
            while not player.quitting:
                writer.write(b"\n>> ")
                await writer.drain()

                try:
                    line = await reader.readline()
                except (ConnectionResetError, BrokenPipeError, OSError):
                    break

                if not line:
                    break

                await handle_command(line.decode(errors="replace"), player, game_state)

        finally:
            game_state.players.pop(name, None)
            db.save_player_data(player)
            await _follow_cleanup(player)
            await _party_leave_cleanup(player)
            for p in game_state.players.values():
                await p.send(f"*** {name} has left the MUD. ***")

    except (ConnectionResetError, BrokenPipeError, OSError):
        pass
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except OSError:
            pass
        print(f"{'?' if name is None else name} disconnected from {addr}")


async def main():
    db.init_db()
    server = await asyncio.start_server(handle_client, HOST, PORT)
    addrs = ", ".join(str(s.getsockname()) for s in server.sockets)
    print(f"WRMS MUD v{VERSION} running on {addrs}")
    print(f"Connect with:  python3 client.py")
    asyncio.create_task(_hostile_check_loop())
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
