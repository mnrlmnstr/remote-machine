import asyncio
import time
import sys
import tty

from concurrent.futures import ProcessPoolExecutor

from pybricksdev.connections.pybricks import PybricksHub, StatusFlag
from pybricksdev.ble import find_device
from aiohttp import web

from rtcbot import RTCConnection, getRTCBotJS, CVCamera, CVDisplay

camera = CVCamera()
loop = asyncio.get_event_loop()
routes = web.RouteTableDef()

conn = RTCConnection()
conn.video.putSubscription(camera)

gamepad_axes = []


@conn.subscribe
def on_message(msg):
    global gamepad_axes
    gamepad_axes = msg


@routes.get('/rtcbot.js')
async def rtcbotjs(request):
    return web.Response(content_type='application/javascript', text=getRTCBotJS())


@routes.post('/connect')
async def connect(request):
    client_offer = await request.json()
    server_response = await conn.getLocalDescription(client_offer)
    return web.json_response(server_response)


@routes.get('/')
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
                <video autoplay playsinline muted controls></video>
            </main>
            <script>
                var conn = new rtcbot.RTCConnection();
                
                conn.video.subscribe(function(stream) {
                    document.querySelector("video").srcObject = stream;
                });

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

    global gamepad_axes
    while True:
        await asyncio.sleep(0.1)

        axes = list(gamepad_axes)
        if bool(axes):
            command = f'd:{axes[1]}:{axes[3]};'
            await hub.write(str(command).encode())


async def cleanup():
    await conn.close()


app = web.Application()
app.add_routes(routes)
app.on_shutdown.append(cleanup)

loop.create_task(hub_init())
web.run_app(app, loop=loop)

loop.run_forever()
