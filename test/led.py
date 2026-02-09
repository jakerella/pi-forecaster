import time
import board
import adafruit_dotstar
import sys

DOTSTAR_DATA = board.D5
DOTSTAR_CLOCK = board.D6
DOTSTAR_COUNT = 3

dots = adafruit_dotstar.DotStar(DOTSTAR_CLOCK, DOTSTAR_DATA, DOTSTAR_COUNT)

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "help":
        print("Usage: python led.py <color>")
        print("  color: 'rotate' or 'red,green,blue' with values 0-255")
        print("         Or include a 4th option for brightness: '80,200,100,0.5'")
        sys.exit(1)

    if len(sys.argv) < 2:
        color = "rotate"
    else:
        color = sys.argv[1]

    if color == "rotate":
        rotate_colors()
    else:
        change_color(color)
        while True:
            new_color = input("Press ctrl+C to quit, or change color to: ")
            change_color(new_color)


def change_color(color):
    colors = color.split(",")
    brightness = 0.5
    r, g, b = int(colors[0]), int(colors[1]), int(colors[2])
    if len(colors) > 3:
        brightness = float(colors[3])
    for i in range(DOTSTAR_COUNT):
        dots[i] = (r, g, b, brightness)

def wheel(pos, brightness=0.5):
    if pos < 0 or pos > 255:
        return (0, 0, 0)
    if pos < 85:
        return (255 - pos * DOTSTAR_COUNT, pos * DOTSTAR_COUNT, 0)
    if pos < 170:
        pos -= 85
        return (0, 255 - pos * DOTSTAR_COUNT, pos * DOTSTAR_COUNT)
    pos -= 170
    return (pos * DOTSTAR_COUNT, 0, 255 - pos * DOTSTAR_COUNT, brightness)

def rotate_colors():
    while True:
        for j in range(255):
            for i in range(DOTSTAR_COUNT):
                rc_index = (i * 256 // DOTSTAR_COUNT) + j * 5
                dots[i] = wheel(rc_index & 255)
            time.sleep(0.05)

try:
    main()
finally:
    for i in range(DOTSTAR_COUNT):
        dots[i] = (0,0,0,0)