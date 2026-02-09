import time
import board
from digitalio import DigitalInOut, Direction, Pull
import adafruit_dotstar
import pyttsx3
from getWeather import get_forecast_data

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
        set_dot_color((0, 255, 0))
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
                    set_dot_color((0, 255, 0))
                    print("\nWaiting for button press...\n")
            btn_prev_state = btn_state
    finally:
        print("Shitting down forecaster...")
        set_dot_color((255, 0, 0))


def set_dot_color(wheel):
    for i in range(len(dots)):
        dots[i] = wheel


def get_weather(day="today"):
    print("  retrieving weather forecast for " + day + "...")
    set_dot_color((255, 255, 0))

    message = "Unable to retrieve forecast for " + day
    try:
        data = get_forecast_data({ 'date': day })
        message = data.get("forecast", "No forecast was available for " + day)
    except Exception as e:
        print("  ERROR retrieving forecast: " + str(e))
        message = "Unable to retrieve forecast for " + day

    print("  initiating voice playback of message...")
    print("  " + message)
    set_dot_color((0, 0, 255))
    speechEngine.say(message)
    speechEngine.runAndWait()
    speechEngine.stop()
    print("  complete.")
    time.sleep(1)


########################
if __name__=='__main__':
    start()
########################
