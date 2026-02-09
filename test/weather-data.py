import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from forecaster.getWeather import get_forecast_data
import json

def runTest(title, options):
    try:
        print(title)
        result = get_forecast_data(options)
        print(result['forecastDate'])
        print(result['forecast'])
        print(json.dumps(result['options'], indent=4))
        print(json.dumps(result['weatherData'], indent=4))
    except ValueError as ve:
        print("User input error:")
        print(ve)
    except IOError as ioe:
        print("API issue:")
        print(ioe)
    except Exception as e:
        print("Unhandled error:")
        print(e)
        print(traceback.format_exc())

# runTest("EMPTY OPTIONS", {})
# runTest("TODAY", {'lat': 38.89, 'lng': -77.04, 'date': 'today'})
# runTest("TOMORROW", {'date': 'tomorrow'})
runTest("SPECIFIC DATE YYYY-MM-DD", {'date': '2026-02-15'})
# runTest("SPECIFIC DAY", {'date': 'sunday'})
# runTest("INVALID DATE YYYY-MM-DD", {'date': '2026-17-39'})
# runTest("INVALID DATE", {'date': 'sdgdfgherhe'})
