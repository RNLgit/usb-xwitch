import micropython
import select
import sys
micropython.kbd_intr(-1)
while True:
    while sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
        ch = sys.stdin.read(1)
        print("Got " + hex(ord(ch)))
