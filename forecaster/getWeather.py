import json
import os
from datetime import datetime, timedelta
from pytz import timezone
from google import genai
from google.genai import types
import wave
import requests
import base64
import re
from dotenv import load_dotenv

load_dotenv()

CACHE_DIR = os.path.join(os.path.dirname(__file__), '.cache')
WEATHER_FORECAST_CACHE = os.path.join(CACHE_DIR, 'weather_forecast.json')
WEATHER_HISTORY_CACHE = os.path.join(CACHE_DIR, 'weather_historical.json')

with open(os.path.join(os.path.dirname(__file__), 'weather-codes.json')) as f:
    WEATHER_CODES = json.load(f)
with open(os.path.join(os.path.dirname(__file__), 'ai-forecast-instruction.txt')) as f:
    AI_FORECAST_INSTRUCTION = f.read()
with open(os.path.join(os.path.dirname(__file__), 'ai-voice-instruction.txt')) as f:
    AI_VOICE_INSTRUCTION = f.read()

DEFAULT_OPTIONS = {
    'date': 'today',
    'lat': 38.89,
    'lng': -77.04,
    'timezone': 'America/New_York',
    'humidity_break': 0.80,
    'wind_break': 5,
    'high_temp_break': 90,
    'low_temp_break': 30,
    'wind_speed_unit': 'mph',
    'temperature_unit': 'fahrenheit',
    'precipitation_unit': 'inch'
}

FORECAST_TTL = 60 * 60 * 2  # 2 hour timeout in milliseconds
DAYS = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
FIELD_MAP = {
    'time': 'time',
    'temperature_2m': 'actual temperature',
    'apparent_temperature': 'feels like temperature',
    'precipitation_probability': 'probability of precipitation',
    'precipitation': 'precipitation amount',
    'uv_index': 'UV index',
    'cloud_cover': 'cloud cover percent',
    'relative_humidity_2m': 'relative humidity percent',
    'wind_speed_10m': 'wind speed',
    'wind_gusts_10m': 'wind gust speed',
    'wind_direction_10m': 'wind direction degrees'
}


def get_forecast_data(input_options: dict = None):
    """
    Call this function from other modules.

    Args:
      input_options: dict with any keys from DEFAULT_OPTIONS. Any omitted keys will use default value.

    Returns:
      dict with keys: 'forecast', 'forecastDate', and the input options.

    Raises:
      ValueError on user input issues.
      IOError on external API errors.
    """
    options = parse_input_and_validate(input_options or {})
    forecast_simple_date = options['forecastDate'].strftime('%Y-%m-%d')

    forecast = get_cached_forecast(options)
    if forecast:
        print(f"Using cached forecast for {options['lat']}, {options['lng']} on {options['forecastDate']}")
        return {
            'forecast': forecast['text'],
            'audioFile': forecast['audio_file'],
            'forecastDate': forecast_simple_date,
            'weatherData': None,
            'options': {k: v for k, v in options.items() if k not in ['forecastDate', 'now']}
        }
    
    forecast = f"Unable to retrieve forecast for {options['date']}"

    historical_data = get_historical_data(options)

    weather_data = get_weather_data(options)
    weather_data['current date and time'] = options['now'].strftime('%B %d, %Y %H:%M')
    weather_data['previous year weekly averages'] = historical_data

    forecast = get_forecast(options, weather_data)

    return {
        'forecast': forecast['text'],
        'audioFile': forecast['audio_file'],
        'forecastDate': forecast_simple_date,
        'weatherData': weather_data,
        'options': {k: v for k, v in options.items() if k not in ['forecastDate', 'now']}
    }


def ensure_cache_dir():
    os.makedirs(CACHE_DIR, exist_ok=True)


def load_cache(cache_file):
    ensure_cache_dir()
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return json.load(f)
    return {}


def save_cache(cache_file, data):
    ensure_cache_dir()
    with open(cache_file, 'w') as f:
        json.dump(data, f)


def parse_input_and_validate(input_dict: dict):
    # Normalize input keys to lowercase and merge with defaults
    query_params = {}
    for key, value in (input_dict or {}).items():
        name = key.lower()
        if name in DEFAULT_OPTIONS and value is not None:
            if name in ['lat', 'lng', 'humidity_break', 'wind_break', 'high_temp_break', 'low_temp_break']:
                try:
                    query_params[name] = float(value)
                except (ValueError, TypeError):
                    pass
            else:
                query_params[name] = str(value).lower()

    options = {**DEFAULT_OPTIONS, **query_params}

    if not isinstance(options['lat'], (int, float)) or not isinstance(options['lng'], (int, float)) or \
       options['lat'] < -90 or options['lat'] > 90 or options['lng'] < -180 or options['lng'] > 180:
        raise ValueError(f"Invalid lat, lng inputs: {options['lat']}, {options['lng']}")

    tz = timezone(options['timezone'])
    now = datetime.now(tz)
    forecast_date = now
    date_str = options['date']

    if re.search("^[0-9]{4}-[01][0-9]-[0-3][0-9]$", date_str):  # YYYY-MM-DD format
        try:
            forecast_date = datetime.strptime(date_str, '%Y-%m-%d').replace(tzinfo=tz)
            diff = (forecast_date.date() - now.date()).days
            if diff < 0 or diff > 6:
                raise ValueError(f"Date input is out of range: {date_str}")
        except ValueError:
            raise ValueError(f"Invalid YYYY-MM-DD date input: {date_str}")
    elif date_str in DAYS:
        curr_day_index = DAYS.index(now.strftime("%A").lower())
        desired_day_index = DAYS.index(date_str)
        days_to_add = (desired_day_index - curr_day_index) % 7
        forecast_date = now + timedelta(days=days_to_add)
    elif date_str == 'tomorrow':
        forecast_date = now + timedelta(days=1)
    elif date_str != 'today':
        raise ValueError(f"Invalid date input for forecast: {date_str}")

    return {**options, 'forecastDate': forecast_date, 'now': now}


def get_cached_forecast(options):
    forecast_cache = load_cache(WEATHER_FORECAST_CACHE)
    today = options['now'].strftime('%Y-%m-%d')
    forecast_simple_date = options['forecastDate'].strftime('%Y-%m-%d')

    forecast = None

    if forecast_simple_date in forecast_cache:
        coord = f"{options['lat']}_{options['lng']}"
        if (
            coord in forecast_cache[forecast_simple_date] and 
            int(datetime.now().timestamp()) <= forecast_cache[forecast_simple_date][coord]['exp']
            ):
            forecast = {
                'text': forecast_cache[forecast_simple_date][coord]['txt'],
                'audio_file': forecast_cache[forecast_simple_date][coord]['wav']
            }

    return forecast


def get_historical_data(options):
    historical_cache = load_cache(WEATHER_HISTORY_CACHE)
    last_year = str(int(options['forecastDate'].strftime('%Y')) - 1)
    forecast_week = int(options['forecastDate'].strftime('%W')) - 1  # zero-based weeks in cache
    coord = f"{options['lat']}_{options['lng']}"

    if last_year in historical_cache and coord in historical_cache[last_year]:
        print(f"Using cached historical data for {last_year} at {coord}")
        return {
            'average low temperature': historical_cache[last_year][coord][forecast_week][0],
            'average high temperature': historical_cache[last_year][coord][forecast_week][1]
        }

    print(f"Retrieving historical weather data for {last_year} at {coord}")
    url = 'https://archive-api.open-meteo.com/v1/archive?' + '&'.join([
        'daily=temperature_2m_max,temperature_2m_min,precipitation_sum',
        f"latitude={options['lat']}",
        f"longitude={options['lng']}",
        f"start_date={last_year}-01-01",
        f"end_date={last_year}-12-31",
        'timezone=auto',
        f"temperature_unit={options['temperature_unit']}",
        f"precipitation_unit={options['precipitation_unit']}"
    ])

    resp = requests.get(url)
    if resp.status_code > 299:
        raise IOError(f"Unable to get historical weather data ({resp.status_code}): {resp.text}")

    historical_data = resp.json()

    if last_year not in historical_cache:
        historical_cache[last_year] = {}
    historical_cache[last_year][coord] = []

    day_count = 0
    week_high_total = 0
    week_low_total = 0
    for i in range(len(historical_data['daily']['time'])):
        week_high_total += historical_data['daily']['temperature_2m_max'][i]
        week_low_total += historical_data['daily']['temperature_2m_min'][i]
        day_count += 1
        if day_count > 6:
            historical_cache[last_year][coord].append([
                round(week_low_total / 7),
                round(week_high_total / 7),
            ])
            day_count = 0
            week_high_total = 0
            week_low_total = 0

    print(f"Caching historical data for {last_year} at {coord}")
    save_cache(WEATHER_HISTORY_CACHE, historical_cache)

    return {
        'average low temperature': historical_cache[last_year][coord][forecast_week][0],
        'average high temperature': historical_cache[last_year][coord][forecast_week][1]
    }


def get_weather_data(options):
    prev_date = (options['forecastDate'] - timedelta(days=1)).strftime('%Y-%m-%d')
    next_date = (options['forecastDate'] + timedelta(days=1)).strftime('%Y-%m-%d')

    url = 'https://api.open-meteo.com/v1/forecast?' + '&'.join([
        'hourly=temperature_2m,apparent_temperature,precipitation_probability,precipitation,uv_index,cloud_cover,relative_humidity_2m,wind_speed_10m,wind_direction_10m,wind_gusts_10m,weather_code',
        # we don't use "current" or "daily" data right now, but we could in the future
        # 'current=temperature_2m,apparent_temperature,precipitation_probability,precipitation,weather_code,cloud_cover,wind_speed_10m,wind_direction_10m',
        # 'daily=sunset,sunrise,temperature_2m_max,precipitation_sum,winddirection_10m_dominant',
        f"latitude={options['lat']}",
        f"longitude={options['lng']}",
        f"start_date={prev_date}",
        f"end_date={next_date}",
        f"timezone={options['timezone']}",
        f"wind_speed_unit={options['wind_speed_unit']}",
        f"temperature_unit={options['temperature_unit']}",
        f"precipitation_unit={options['precipitation_unit']}"
    ])

    resp = requests.get(url)
    if resp.status_code > 299:
        raise IOError(f"Unable to get weather forecast data ({resp.status_code}): {resp.text}")

    raw_data = resp.json()
    weather_data = {'previous day': [], 'forecast day': [], 'following day': []}
    elements = [key for key in raw_data['hourly'].keys() if key in FIELD_MAP]

    for i in range(len(raw_data['hourly']['time'])):
        day = 'previous day'
        if i > 23:
            day = 'forecast day'
        if i > 47:
            day = 'following day'

        hourly_data = {}
        for e in elements:
            hourly_data[FIELD_MAP[e]] = raw_data['hourly'][e][i]

        weather_code = WEATHER_CODES[str(raw_data['hourly']['weather_code'][i])]
        hourly_data['weather description'] = weather_code['description']

        if weather_code['category'] in ['rain', 'snow']:
            hourly_data['precipitation type'] = weather_code['category']
        elif raw_data['hourly']['precipitation_probability'][i] > 4:
            if raw_data['hourly']['temperature_2m'][i] < 35:
                hourly_data['precipitation type'] = 'snow'
            else:
                hourly_data['precipitation type'] = 'rain'

        weather_data[day].append(hourly_data)

    return weather_data


def get_forecast(options, data):
    forecast_date_simple = options['forecastDate'].strftime('%Y-%m-%d')
    coord = f"{options['lat']}_{options['lng']}"
    prompt = 'Generate a weather forecast'

    if forecast_date_simple == options['now'].strftime('%Y-%m-%d'):
        prompt = 'Generate a weather forecast for today. Include current conditions as well as any significant weather activity for the remainder of today. '
        if int(options['forecastDate'].strftime('%H')) > 17:
            prompt += 'Include a very brief summary of the weather for the following day as well.'
    else:
        prompt = f"Generate a weather forecast for {options['forecastDate'].strftime('%A')} whose date is {forecast_date_simple}. This is a date in the future. Do not include any information about current conditions. Do not use terms like \"this morning\" or \"this afternoon\" and instead use \"{options['forecastDate'].strftime('%A')} morning\" or \"{options['forecastDate'].strftime('%A')} afternoon\". Your forecast should cover weather for the entire day on {forecast_date_simple}, and should not include weather for any other day."

    print(f'Generating a weather forecast using prompt:\n{prompt}')

    client = genai.Client(api_key=os.getenv('GEN_AI_KEY'))

    forecastResponse = client.models.generate_content(
        model = "gemini-3-flash-preview",
        contents = [
            {'text': prompt},
            {'inlineData': {'data': base64.b64encode(json.dumps(data).encode()).decode(), 'mimeType': 'application/json'}}
        ],
        config = types.GenerateContentConfig(system_instruction=AI_FORECAST_INSTRUCTION),
    )
    forecast = forecastResponse.text

    voiceResponse = client.models.generate_content(
        model = "gemini-2.5-flash-preview-tts",
        contents = AI_VOICE_INSTRUCTION + "\n" + forecast,
        config = types.GenerateContentConfig(
            response_modalities = ["AUDIO"],
            speech_config = types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config = types.PrebuiltVoiceConfig(voice_name = 'Erinome')
                )
            )
        )
    )

    wave_filename = os.path.join(CACHE_DIR, f"{forecast_date_simple}_{coord}.wav")
    voiceData = voiceResponse.candidates[0].content.parts[0].inline_data.data
    create_wave_file(wave_filename, voiceData)

    forecast_cache = load_cache(WEATHER_FORECAST_CACHE)
    print(f"Caching forecast data for location {coord} on {forecast_date_simple}")

    if forecast_date_simple not in forecast_cache:
        forecast_cache[forecast_date_simple] = {}

    forecast_cache[forecast_date_simple][coord] = {
        'exp': int(datetime.now().timestamp()) + FORECAST_TTL,
        'txt': forecast,
        'wav': wave_filename
    }
    save_cache(WEATHER_FORECAST_CACHE, forecast_cache)

    return { 'text': forecast, 'audio_file': wave_filename }


def create_wave_file(filename, data, channels=1, rate=24000, sample_width=2):
    ensure_cache_dir()
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(data)

