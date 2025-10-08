"""
OpenWeatherMap API service for py_home

Provides current weather data and forecasts.

Setup:
1. Get API key from https://openweathermap.org/api
2. Add to config/.env: OPENWEATHER_API_KEY=your_key
3. Configure location in config/config.yaml

API Docs: https://openweathermap.org/api
"""

import requests
import logging

logger = logging.getLogger(__name__)


class OpenWeatherAPI:
    """
    OpenWeatherMap API client

    Provides current weather and forecast data.
    """

    BASE_URL = "https://api.openweathermap.org/data/2.5"

    def __init__(self, api_key=None, units=None, zip_code=None):
        from lib.config import config

        self.api_key = api_key or config['openweather']['api_key']
        self.units = units or config['openweather'].get('units', 'imperial')
        # Use home location coordinates as default (not hardcoded zip)
        self.home_lat = config['locations']['home']['lat']
        self.home_lon = config['locations']['home']['lng']
        self.zip_code = zip_code  # Only use if explicitly provided

        if not self.api_key:
            raise ValueError(
                "OpenWeather API key not configured. "
                "Add OPENWEATHER_API_KEY to config/.env"
            )

    def _get(self, endpoint, params=None):
        """Make GET request to OpenWeather API"""
        if params is None:
            params = {}

        params['appid'] = self.api_key
        params['units'] = self.units

        url = f"{self.BASE_URL}/{endpoint}"
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()

        return resp.json()

    def get_current_weather(self, location=None, lat=None, lon=None):
        """
        Get current weather for a location

        Args:
            location: Zip code (e.g. "60601,us") or city name (e.g. "Chicago,us")
            lat: Latitude (alternative to location)
            lon: Longitude (alternative to location)

        Returns:
            dict: {
                'temp': float,
                'feels_like': float,
                'temp_min': float,
                'temp_max': float,
                'humidity': int (percent),
                'pressure': int (hPa),
                'conditions': str (description),
                'conditions_main': str (main category),
                'city': str,
                'is_cold': bool (< 40°F),
                'is_precipitation': bool (rain or snow),
                'wind_speed': float (mph or m/s),
                'clouds': int (percent)
            }

        Example:
            >>> weather = api.get_current_weather("60601,us")
            >>> print(f"Chicago: {weather['temp']}°F, {weather['conditions']}")
        """
        params = {}

        if lat and lon:
            params['lat'] = lat
            params['lon'] = lon
        elif location:
            if ',' in location:
                # Zip code or city,country format
                params['q'] = location
            else:
                # Just zip code, assume US
                params['zip'] = f"{location},us"
        else:
            # Use home location coordinates as default
            params['lat'] = self.home_lat
            params['lon'] = self.home_lon

        data = self._get('weather', params)

        # Extract key fields
        result = {
            'temp': data['main']['temp'],
            'feels_like': data['main']['feels_like'],
            'temp_min': data['main']['temp_min'],
            'temp_max': data['main']['temp_max'],
            'humidity': data['main']['humidity'],
            'pressure': data['main']['pressure'],
            'conditions': data['weather'][0]['description'],
            'conditions_main': data['weather'][0]['main'],
            'city': data['name'],
            'wind_speed': data['wind']['speed'],
            'clouds': data['clouds']['all'],

            # Derived fields (useful for automations)
            'is_cold': data['main']['temp'] < 40 if self.units == 'imperial' else data['main']['temp'] < 4,
            'is_precipitation': data['weather'][0]['main'] in ['Rain', 'Snow', 'Drizzle', 'Thunderstorm'],
        }

        logger.info(
            f"Weather for {result['city']}: {result['temp']}°{'F' if self.units == 'imperial' else 'C'}, "
            f"{result['conditions']}"
        )

        return result

    def get_forecast(self, location=None, lat=None, lon=None, days=5):
        """
        Get weather forecast (5 days, 3-hour intervals)

        Args:
            location: Zip code or city name
            lat: Latitude (alternative)
            lon: Longitude (alternative)
            days: Number of days (max 5)

        Returns:
            list: List of forecast dicts, each with:
                {
                    'dt': timestamp,
                    'dt_txt': formatted datetime,
                    'temp': float,
                    'feels_like': float,
                    'humidity': int,
                    'conditions': str,
                    'conditions_main': str,
                    'pop': float (probability of precipitation 0-1),
                    'rain': float (mm in 3h),
                    'snow': float (mm in 3h),
                    'wind_speed': float
                }

        Example:
            >>> forecast = api.get_forecast("Chicago,us")
            >>> for period in forecast[:8]:  # Next 24 hours
            >>>     print(f"{period['dt_txt']}: {period['temp']}°F, {period['conditions']}")
        """
        params = {}

        if lat and lon:
            params['lat'] = lat
            params['lon'] = lon
        elif location:
            if ',' in location:
                params['q'] = location
            else:
                params['zip'] = f"{location},us"
        else:
            # Use home location coordinates as default
            params['lat'] = self.home_lat
            params['lon'] = self.home_lon

        # Limit to requested days (each day has 8 periods of 3 hours)
        params['cnt'] = min(days * 8, 40)

        data = self._get('forecast', params)

        forecasts = []
        for item in data['list']:
            forecast = {
                'dt': item['dt'],
                'dt_txt': item['dt_txt'],
                'temp': item['main']['temp'],
                'feels_like': item['main']['feels_like'],
                'temp_min': item['main']['temp_min'],
                'temp_max': item['main']['temp_max'],
                'humidity': item['main']['humidity'],
                'conditions': item['weather'][0]['description'],
                'conditions_main': item['weather'][0]['main'],
                'pop': item.get('pop', 0),  # Probability of precipitation
                'wind_speed': item['wind']['speed'],
                'clouds': item['clouds']['all'],
            }

            # Optional rain/snow data
            if 'rain' in item:
                forecast['rain'] = item['rain'].get('3h', 0)
            if 'snow' in item:
                forecast['snow'] = item['snow'].get('3h', 0)

            forecasts.append(forecast)

        logger.info(f"Retrieved {len(forecasts)} forecast periods for {data['city']['name']}")

        return forecasts

    def get_weather_summary(self, location=None):
        """
        Get simplified weather summary for voice/notifications

        Returns:
            str: Human-readable weather summary

        Example:
            >>> summary = api.get_weather_summary("Chicago,us")
            >>> print(summary)
            "Chicago: 72°F, partly cloudy. High: 75°F, Low: 68°F."
        """
        weather = self.get_current_weather(location)

        summary = (
            f"{weather['city']}: {weather['temp']:.0f}°{'F' if self.units == 'imperial' else 'C'}, "
            f"{weather['conditions']}. "
            f"High: {weather['temp_max']:.0f}°, Low: {weather['temp_min']:.0f}°. "
            f"Humidity: {weather['humidity']}%."
        )

        if weather['is_cold']:
            summary += " Bundle up!"

        if weather['is_precipitation']:
            summary += " Bring an umbrella!"

        return summary


# Singleton instance
_weather = None

def get_weather():
    """Get or create OpenWeather API instance"""
    global _weather
    if _weather is None:
        _weather = OpenWeatherAPI()
    return _weather


# Convenience functions
def get_current_weather(location=None, lat=None, lon=None):
    """Get current weather for location"""
    return get_weather().get_current_weather(location, lat, lon)


def get_forecast(location=None, lat=None, lon=None, days=5):
    """Get weather forecast"""
    return get_weather().get_forecast(location, lat, lon, days)


def get_weather_summary(location=None):
    """Get human-readable weather summary"""
    return get_weather().get_weather_summary(location)


__all__ = [
    'OpenWeatherAPI',
    'get_weather',
    'get_current_weather',
    'get_forecast',
    'get_weather_summary'
]
