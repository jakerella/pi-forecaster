import time
import board
from digitalio import DigitalInOut, Direction, Pull
import adafruit_dotstar
import pyttsx3
import os
import time
import requests

print("\nStarting Pi-Forecaster...")

print("  getting LED dots...")
DOTSTAR_DATA = board.D5
DOTSTAR_CLOCK = board.D6
dots = adafruit_dotstar.DotStar(DOTSTAR_CLOCK, DOTSTAR_DATA, 3, brightness=0.01)

print("  getting button...")
button = DigitalInOut(board.D17)
button.direction = Direction.INPUT
button.pull = Pull.UP

print("  initializing text-to-speech...")
speechEngine = pyttsx3.init()
speechEngine.setProperty("voice", "gmw/en-us-nyc")

def start():
    try:
        setDotColor((0, 255, 0))
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
                    getWeather(day)
                    setDotColor((0, 255, 0))
                    print("\nWaiting for button press...\n")
            btn_prev_state = btn_state
    finally:
        setDotColor((255, 0, 0))


def setDotColor(wheel):
    for i in range(len(dots)):
        dots[i] = wheel


def getWeather(day="today"):
    print("  retrieving weather forecast for " + day + "...")
    setDotColor((255, 255, 0))

    response = requests.get(
        "https://jordankasper.com/.netlify/functions/getWeather?date=" + day,
        headers = { "Authorization": os.getenv("WEATHER_KEY", None) }
    )
    data = response.json()
    message = "No forecast available for " + day
    if response.status_code == 200:
        print(data["forecast"])
        message = data["forecast"]
    else:
        print("ERROR from forecast service (" + response.status_code + "): " + data["message"])
        message = data["message"]

    print("  initiating voice playback...")
    setDotColor((0, 0, 255))
    speechEngine.say(message)
    speechEngine.runAndWait()
    speechEngine.stop()
    print("  complete.")
    time.sleep(1)


########################
if __name__=='__main__':
    start()
########################
