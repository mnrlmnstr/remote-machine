import sys

from pybricks.hubs import TechnicHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction, Color

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
    print(1)