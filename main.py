import asyncio
from player import Player
import game_state
from commands import handle_command, display_room

VERSION = "0.10"
HOST = "0.0.0.0"
PORT = 4000


async def handle_client(reader, writer):
    addr = writer.get_extra_info("peername")
    print(f"Connection from {addr}")

    writer.write(b"Enter your name: ")
    await writer.drain()

    try:
        name_bytes = await asyncio.wait_for(reader.readline(), timeout=30)
    except asyncio.TimeoutError:
        writer.close()
        return

    name = name_bytes.decode(errors="replace").strip()
    if not name:
        writer.write(b"No name entered. Goodbye.\n")
        await writer.drain()
        writer.close()
        return

    if name in game_state.players:
        writer.write(f"Name '{name}' is already taken. Try another.\n".encode())
        await writer.drain()
        writer.close()
        return

    player = Player(name, "menu", writer, gold=0, inventory=[], max_inventory=10)
    game_state.players[name] = player
    await player.send(f"WRMS MUD v{VERSION}")

    for p in game_state.players.values():
        if p is not player:
            await p.send(f"*** {name} has entered the MUD. ***")

    await display_room("menu", player)

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
        for p in game_state.players.values():
            await p.send(f"*** {name} has left the MUD. ***")
        try:
            writer.close()
            await writer.wait_closed()
        except OSError:
            pass
        print(f"{name} disconnected from {addr}")


async def main():
    server = await asyncio.start_server(handle_client, HOST, PORT)
    addrs = ", ".join(str(s.getsockname()) for s in server.sockets)
    print(f"WRMS MUD v{VERSION} running on {addrs}")
    print(f"Connect with:  python3 client.py")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
