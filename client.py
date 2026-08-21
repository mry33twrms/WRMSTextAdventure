import asyncio
import os
import sys
import termios
import threading
import tty

HOST = "127.0.0.1"
PORT = 4000

PWD_SIGNAL = b"\x1bPWD"   # server sends this to activate star-masking for next input


async def main():
    try:
        reader, writer = await asyncio.open_connection(HOST, PORT)
    except ConnectionRefusedError:
        print(f"Could not connect to {HOST}:{PORT} — is the server running?")
        print("Start it with:  python3 main.py")
        return

    loop = asyncio.get_event_loop()
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    pending_input = ""    # characters the user has typed but not yet sent
    current_prompt = ""   # the prompt string currently shown (e.g. ">> ")
    password_mode  = False  # when True, echo * instead of actual characters
    char_queue: asyncio.Queue[bytes] = asyncio.Queue()

    def read_stdin():
        """Blocking stdin reader in a daemon thread; feeds bytes to char_queue."""
        while True:
            try:
                ch = os.read(fd, 1)
                if not ch:
                    break
                loop.call_soon_threadsafe(char_queue.put_nowait, ch)
            except OSError:
                break

    try:
        tty.setraw(fd)
        threading.Thread(target=read_stdin, daemon=True).start()

        async def recv():
            nonlocal pending_input, current_prompt, password_mode
            while True:
                data = await reader.read(4096)
                if not data:
                    sys.stdout.write('\r\n[Disconnected from server]\r\n')
                    sys.stdout.flush()
                    return

                # Detect password-mode signal and strip it before display
                if PWD_SIGNAL in data:
                    data = data.replace(PWD_SIGNAL, b"")
                    password_mode = True

                msg = data.decode(errors="replace")

                # If the server's data ends with the prompt, strip it so we
                # control where it appears (avoids double-printing on restore).
                if msg.endswith(">> "):
                    msg = msg[:-3]
                    current_prompt = ">> "

                # Raw mode needs explicit \r before every \n.
                msg = msg.replace('\r\n', '\n').replace('\n', '\r\n')

                # Clear the current input line, print the server message,
                # then restore the prompt + pending input (masked if needed).
                masked = '*' * len(pending_input) if password_mode else pending_input
                sys.stdout.write('\r\033[K')
                sys.stdout.write(msg)
                sys.stdout.write(current_prompt + masked)
                sys.stdout.flush()

        async def send():
            nonlocal pending_input, current_prompt, password_mode
            while True:
                raw = await char_queue.get()
                char = raw.decode('ascii', errors='replace')

                if char in ('\r', '\n'):
                    line = pending_input
                    pending_input = ""
                    current_prompt = ""
                    password_mode = False   # always clear after Enter
                    sys.stdout.write('\r\n')
                    sys.stdout.flush()
                    writer.write((line + '\n').encode())
                    await writer.drain()

                elif char in ('\x7f', '\x08'):  # backspace / delete
                    if pending_input:
                        pending_input = pending_input[:-1]
                        sys.stdout.write('\b \b')
                        sys.stdout.flush()

                elif char == '\x03':  # Ctrl+C
                    raise KeyboardInterrupt

                elif char == '\x04':  # Ctrl+D
                    return

                elif char == '\x1b':  # escape sequence (arrow keys, etc.) — eat next 2 bytes
                    await char_queue.get()
                    await char_queue.get()

                elif char.isprintable():
                    pending_input += char
                    sys.stdout.write('*' if password_mode else char)
                    sys.stdout.flush()

        recv_task = asyncio.create_task(recv())
        send_task = asyncio.create_task(send())

        done, pending_tasks = await asyncio.wait(
            [recv_task, send_task], return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending_tasks:
            task.cancel()

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        try:
            writer.close()
            await writer.wait_closed()
        except OSError:
            pass
        sys.stdout.write('\r\n')


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[Quit]")
