import usys

from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction

left = Motor(Port.A, Direction.COUNTERCLOCKWISE)
right = Motor(Port.B, Direction.COUNTERCLOCKWISE)

left.control.limits(acceleration=1000)
right.control.limits(acceleration=1000)

while True:
    left.run(800)
    right.run(800)

    print('received', usys.stdin.read(1))
