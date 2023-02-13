import asyncio
import sys
import tty

from pybricksdev.connections.pybricks import PybricksHub, StatusFlag
from pybricksdev.ble import find_device


def read_key():
    fd = sys.stdin.fileno()
    tty.setraw(fd)
    return sys.stdin.read(1)


async def main():
    print('main: Start')

    hub = PybricksHub()

    device = await find_device()
    await hub.connect(device)
    print('Device: ', device)

    try:
        forwarder_task = asyncio.create_task(forwarder(hub))
        try:
            await hub.run('tank.py')
        finally:
            forwarder_task.cancel()
    finally:
        # Disconnect from the hub
        await hub.disconnect()
        print('main: Stop')


async def forwarder(hub: PybricksHub):
    print("forwarder: Start")

    queue = asyncio.Queue()

    # wait for user program on the hub to start
    with hub.status_observable.subscribe(lambda s: queue.put_nowait(s)):
        while True:
            status = await queue.get()

            if status & StatusFlag.USER_PROGRAM_RUNNING:
                break

    print('forwarder: Hub Running')

    loop = asyncio.get_running_loop()

    # Keyboard command input loop
    while True:
        command = await loop.run_in_executor(None, read_key)
        await hub.write(bytes([ord(command)]))

# start it up
asyncio.run(main())
