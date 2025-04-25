from datetime import datetime
from meteostat import Point, Daily
import time
import pandas as pd

weather_cache = {}

def get_todays_forecast(lat, long, date, retries=3):
    key = (round(lat, 2), round(long, 2), date)
    if key in weather_cache:
        return weather_cache[key]
    for attempt in range(retries + 1):
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            location = Point(lat, long)
            data = Daily(location, date_obj, date_obj).fetch()
            if data.empty:
                weather_cache[key] = None
                return None
            forecast = data.iloc[0]
            '''
            result = {
                "temperature_avg_C": forecast['tavg'],
                "temperature_min_C": forecast['tmin'],
                "temperature_max_C": forecast['tmax'],
                "precipitation_mm": forecast['prcp']
                "wind_speed_kph": forecast['wspd'],
                "snow_mm": forecast['snow']
            }
            '''
            weather_keys = {
                'temperature_avg_C': 'tavg',
                'temperature_min_C': 'tmin',
                'temperature_max_C': 'tmax',
                'precipitation_mm': 'prcp',
                'wind_speed_kph': 'wspd',
                'snow_mm': 'snow'
            }
            result = {
                k: 0.0 if pd.isna(forecast.get(v)) else forecast.get(v)
                for k, v in weather_keys.items()
            }
            weather_cache[key] = result
            return result
        except Exception:
            if attempt < retries:
                time.sleep(1)
            else:
                weather_cache[key] = None
                return None

def get_weather_features_for_user_input(lat_o, lon_o, lat_d, lon_d, date_str):
    origin = get_todays_forecast(lat_o, lon_o, date_str)
    dest = get_todays_forecast(lat_d, lon_d, date_str)
    if origin is None or dest is None:
        return None
    features = {}
    for k, v in origin.items():
        features[f"origin_{k}"] = v
    for k, v in dest.items():
        features[f"dest_{k}"] = v
    return features
