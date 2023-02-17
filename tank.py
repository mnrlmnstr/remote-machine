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

hub.light.on(Color.GREEN)

speed = 0
max_speed = 1500
step = 250
command_buffer = ''


def input_handler(command):
    command_list = command.split(':')

    if command_list[0] == "d":
        try:
            left_speed = float(command_list[1]) * -1500
            right_speed = float(command_list[2]) * -1500

            if left_speed == 0:
                left.stop()
            else:
                left.run(left_speed)
                print('l:', left.speed())

            if right_speed == 0:
                right.stop()
            else:
                right.run(right_speed)
                print('r:', right.speed())

        except ValueError:
            print("Skip Invalid command {}".format(command))


def update_input(char):
    global command_buffer
    if char == ';':
        input_handler(command_buffer)
        command_buffer = ''
    else:
        command_buffer += char


while True:
    while gamepad.poll(1):
        char = stdin.read(1)
        if char is not None:
            update_input(char)
