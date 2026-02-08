import time
import board
from digitalio import DigitalInOut, Direction, Pull
import adafruit_dotstar
import pyttsx3

DOTSTAR_DATA = board.D5
DOTSTAR_CLOCK = board.D6
dots = adafruit_dotstar.DotStar(DOTSTAR_CLOCK, DOTSTAR_DATA, 3, brightness=0.01)

button = DigitalInOut(board.D17)
button.direction = Direction.INPUT
button.pull = Pull.UP

speechEngine = pyttsx3.init()

def setDots(wheel):
    for i in range(len(dots)):
        dots[i] = wheel

def getWeather():
    print("  button pressed, getting weather forecast...")
    setDots((255, 0, 0))
    time.sleep(3)
    print("  voicing forecast.")
    setDots((0, 0, 255))
    speechEngine.say('Hello! This is the current forecast.')
    speechEngine.runAndWait()
    speechEngine.stop()
    time.sleep(2)

setDots((0, 255, 0))
print("Waiting for button press...\n")
while True:
    if not button.value:
        getWeather()
        setDots((0, 255, 0))
        print("Waiting for button press...")
    time.sleep(0.2)