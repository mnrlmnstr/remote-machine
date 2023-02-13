import asyncio
from aiohttp import web
routes = web.RouteTableDef()

from rtcbot import RTCConnection, getRTCBotJS

# For this example, we use just one global connection
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

conn = RTCConnection(loop=loop)


def scale(val, src, dst):
    return (float(val - src[0]) / (src[1] - src[0])) * (dst[1] - dst[0]) + dst[0]

@conn.subscribe
def onMessage(msg):  # Called when each message is sent
    axes = list(msg)
    print('left: ', axes[1], 'right: ', axes[3])

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
                    document.getElementById('status').innerText = `${gamepad.id} 
                    Left Stick:
                    X: ${(gamepad.axes[0]).toFixed(4)}
                    Y: ${(gamepad.axes[1]).toFixed(4)}
                    
                    Right Stick:
                    X: ${(gamepad.axes[2]).toFixed(4)}
                    Y: ${(gamepad.axes[3]).toFixed(4)}
                    `
                    conn.put_nowait(gamepad.axes)
                }, 16)
            </script>
        </body>
    </html>
    """)

async def cleanup(app=None):
    await conn.close()


app = web.Application()
app.add_routes(routes)
app.on_shutdown.append(cleanup)
web.run_app(app, loop=loop)