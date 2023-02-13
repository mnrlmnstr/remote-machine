from usys import stdin
from uselect import poll

from pybricks.hubs import TechnicHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction, Color

keyboard = poll()
keyboard.register(stdin)

hub = TechnicHub()
print('Voltage: ', hub.battery.voltage())

left = Motor(Port.B)
right = Motor(Port.A, Direction.COUNTERCLOCKWISE)

WHEEL_DIAMETER = 54

# left.control.limits(acceleration=1000)
# right.control.limits(acceleration=1000)

hub.light.on(Color.GREEN)

speed = 0
max_speed = 1500
step = 250


while True:
    if not keyboard.poll(0):
        continue
    key = stdin.read(1)

    if key == 'w':
        if speed != max_speed:
            speed += step
            left.run(speed)
            right.run(speed)
            print('speed: ', speed)
    elif key == 's':
        if speed != 0:
            speed -= step
            left.run(speed)
            right.run(speed)
            print('speed: ', speed)
    elif key == 'a':
        if left.speed() == 0:
            left.run(speed)
        else:
            left.stop()
    elif key == 'd':
        if right.speed() == 0:
            right.run(speed)
        else:
            right.stop()
    elif left.speed() == 0 and right.speed() == 0:
        left.stop()
        right.stop()

