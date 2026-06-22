class Player:
    def __init__(self, name, current_room, writer):
        self.name = name
        self.current_room = current_room
        self.writer = writer
        self.quitting = False

    async def send(self, msg):
        try:
            self.writer.write((msg + "\n").encode())
            await self.writer.drain()
        except (ConnectionResetError, BrokenPipeError, OSError):
            pass
