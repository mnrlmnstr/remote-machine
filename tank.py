from usys import stdin
from uselect import poll

from pybricks.hubs import TechnicHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction, Color

gamepad = poll()
gamepad.register(stdin)

hub = TechnicHub()
print('Voltage: ', hub.battery.voltage())

left = Motor(Port.B)
right = Motor(Port.A, Direction.COUNTERCLOCKWISE)

# left.control.limits(acceleration=1000)
# right.control.limits(acceleration=1000)

hub.light.on(Color.GREEN)

speed = 0
max_speed = 1500
step = 250
command_buffer = ''


def input_handler(command):
    axes = command.strip('[]').replace('"', '').replace(' ', '').split(',')
    print(axes[1], axes[3])
    left.run(-1500*float(axes[1]))
    right.run(-1500*float(axes[3]))


def update_input(char):
    global command_buffer
    if char == ';':
        input_handler(command_buffer)
        command_buffer = ''
    else:
        command_buffer += char


while True:
    while gamepad.poll(1):  # times out after 100ms
        char = stdin.read(1)
        if char is not None:
            update_input(char)
