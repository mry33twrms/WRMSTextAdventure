import asyncio
import sys

HOST = "127.0.0.1"
PORT = 4000


async def main():
    try:
        reader, writer = await asyncio.open_connection(HOST, PORT)
    except ConnectionRefusedError:
        print(f"Could not connect to {HOST}:{PORT} — is the server running?")
        print("Start it with:  python3 main.py")
        return

    loop = asyncio.get_event_loop()
    stdin_reader = asyncio.StreamReader()
    await loop.connect_read_pipe(
        lambda: asyncio.StreamReaderProtocol(stdin_reader), sys.stdin
    )

    async def recv():
        while True:
            data = await reader.read(4096)
            if not data:
                print("\n[Disconnected from server]")
                return
            print(data.decode(errors="replace"), end="", flush=True)

    async def send():
        while True:
            line = await stdin_reader.readline()
            if not line:
                return
            writer.write(line)
            await writer.drain()

    recv_task = asyncio.create_task(recv())
    send_task = asyncio.create_task(send())

    done, pending = await asyncio.wait(
        [recv_task, send_task], return_when=asyncio.FIRST_COMPLETED
    )
    for task in pending:
        task.cancel()
    try:
        writer.close()
        await writer.wait_closed()
    except OSError:
        pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[Quit]")
