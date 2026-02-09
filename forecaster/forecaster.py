
print("\nStarting Pi-Forecaster...")
print("  setting up LEDs...")

import board
from digitalio import DigitalInOut, Direction, Pull
import adafruit_dotstar

COLOR_OFF = (0, 0, 0, 0)
COLOR_WAITING = (0, 2, 0, 0.1)
COLOR_NOT_READY = (30, 0, 0, 0.1)
COLOR_WORKING = (50, 50, 0, 0.3)
COLOR_TALKING = (0, 0, 50, 0.3)
DOTSTAR_DATA = board.D5
DOTSTAR_CLOCK = board.D6
DOTSTAR_COUNT = 3
dots = adafruit_dotstar.DotStar(DOTSTAR_CLOCK, DOTSTAR_DATA, DOTSTAR_COUNT)

def set_dot_color(color):
    for i in range(DOTSTAR_COUNT):
        dots[i] = color

set_dot_color(COLOR_NOT_READY)

print("  importing other libraries...")
import time
import pyttsx3
from getWeather import get_forecast_data


print("  setting up button...")
button = DigitalInOut(board.D17)
button.direction = Direction.INPUT
button.pull = Pull.UP

print("  initializing text-to-speech...")
speechEngine = pyttsx3.init()
speechEngine.setProperty("voice", "gmw/en-us-nyc")

def start():
    try:
        set_dot_color(COLOR_WAITING)
        print("  setup complete.\n")
        print("Waiting for button press...\n")
        btn_prev_state = button.value
        btn_down_ts = 0
        while True:
            btn_state = button.value
            if btn_state != btn_prev_state:
                if not btn_state:
                    btn_down_ts = time.time()
                else:
                    ts_diff = time.time() - btn_down_ts
                    print("  button held for " + str(ts_diff) + " seconds...")
                    day = "today"
                    if ts_diff > 1.5:
                        day = "tomorrow"
                    get_weather(day)
                    set_dot_color(COLOR_WAITING)
                    print("\nWaiting for button press...\n")
            btn_prev_state = btn_state
    finally:
        print("Shutting down forecaster...")
        set_dot_color(COLOR_OFF)


def get_weather(day="today"):
    print("  retrieving weather forecast for " + day + "...")
    set_dot_color(COLOR_WORKING)

    message = "Unable to retrieve forecast for " + day
    try:
        data = get_forecast_data({ 'date': day })
        message = data.get("forecast", "No forecast was available for " + day)
    except Exception as e:
        print("  ERROR retrieving forecast: " + str(e))
        message = "Unable to retrieve forecast for " + day

    print("  initiating voice playback of message...")
    print("  " + message)
    set_dot_color(COLOR_TALKING)
    speechEngine.say(message)
    speechEngine.runAndWait()
    speechEngine.stop()
    print("  complete.")
    time.sleep(1)


##########################
if __name__ == '__main__':
    start()
##########################
