import asyncio
import time
import sys
import tty

from concurrent.futures import ProcessPoolExecutor

from pybricksdev.connections.pybricks import PybricksHub, StatusFlag
from pybricksdev.ble import find_device
from aiohttp import web

from rtcbot import RTCConnection, getRTCBotJS

loop = asyncio.get_event_loop()

routes = web.RouteTableDef()
conn = RTCConnection()

a = [0, 0, 0, 0]

@conn.subscribe
def onMessage(msg):
    global a
    a = list(msg)

# Serve the RTCBot javascript library at /rtcbot.js
@routes.get("/rtcbot.js")
async def rtcbotjs(request):
    return web.Response(content_type="application/javascript", text=getRTCBotJS())


# This sets up the connection
@routes.post("/connect")
async def connect(request):
    clientOffer = await request.json()
    serverResponse = await conn.getLocalDescription(clientOffer)
    return web.json_response(serverResponse)


@routes.get("/")
async def index(request):
    return web.Response(
        content_type="text/html",
        text="""
    <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, user-scalable=no, initial-scale=1.0, maximum-scale=1.0, minimum-scale=1.0">
            <title>Remote Machine</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <script crossorigin src="https://webrtc.github.io/adapter/adapter-latest.js"></script>
            <script src="/rtcbot.js"></script>
        </head>
        <body class="bg-black text-white">
            <main class="p-4">
                <h3 class="text-2xl font-bold mb-2">Gamepad</h3>
                <div id="status" class="tabular-nums">Press any button</div>
            </main>
            <script>
                var conn = new rtcbot.RTCConnection();

                async function connect() {
                    let offer = await conn.getLocalDescription();

                    // POST the information to /connect
                    let response = await fetch("/connect", {
                        method: "POST",
                        cache: "no-cache",
                        body: JSON.stringify(offer)
                    });

                    await conn.setRemoteDescription(await response.json());

                    console.log("Ready!");
                }
                connect();

                
                setInterval(() => {
                    const gamepads = navigator.getGamepads()
                    const gamepad = gamepads[0]
                    
                    if (gamepad) {
                        document.getElementById('status').innerText = `${gamepad.id} 
                        Left Stick:
                        X: ${(gamepad.axes[0]).toFixed(4)}
                        Y: ${(gamepad.axes[1]).toFixed(4)}
                        
                        Right Stick:
                        X: ${(gamepad.axes[2]).toFixed(4)}
                        Y: ${(gamepad.axes[3]).toFixed(4)}
                        `
                        conn.put_nowait(gamepad.axes)
                    }
                }, 16)
            </script>
        </body>
    </html>
    """)


async def hub_init():
    print('main: Start')

    global hub
    hub = PybricksHub()

    device = await find_device()
    await hub.connect(device)
    print(device)

    try:
        forwarder_task = loop.create_task(forwarder(hub))
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

    global a
    while True:
        await asyncio.sleep(0.1)
        val = f'{a};'
        await hub.write(str(val).encode())


async def cleanup(app=None):
    await conn.close()


app = web.Application()
app.add_routes(routes)
app.on_shutdown.append(cleanup)

loop.create_task(hub_init())
web.run_app(app, loop=loop)

loop.run_forever()
