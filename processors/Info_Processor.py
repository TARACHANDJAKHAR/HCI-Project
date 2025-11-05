import datetime
import requests
from geopy.geocoders import Nominatim
from .Base_Processor import BaseProcessor
import os

weather_codes = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing rime fog",
    51: "drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    56: "light freezing drizzle",
    57: "dense freezing drizzle",
    61: "slight rain",
    63: "moderate rain",
    65: "heavy rain",
    66: "light freezing rain",
    67: "heavy freezing rain",
    71: "slight snow",
    73: "moderate snow",
    75: "heavy snow",
    77: "snow grains",
    80: "slight rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    85: "slight snow showers",
    86: "heavy snow showers",
    95: "thunderstorm",
    96: "thunderstorm with slight hail",
    99: "thunderstorm with heavy hail"
}

geolocator = Nominatim(user_agent="elderly_assistant")

class InfoProcessor(BaseProcessor):
    keywords = ["time", "date", "weather", "news"]

    def handle(self, command: str):
        if "time" in command:
            now = datetime.datetime.now().strftime("%H:%M:%S")
            self.speaker(f"The current time is {now}")

        elif "date" in command:
            today = datetime.date.today().strftime("%B %d, %Y")
            self.speaker(f"Today's date is {today}")

        elif "weather" in command:
            self.get_weather("Surat, India")  # You can make city dynamic later

        elif "news" in command:
            self.get_news()

        return True

    def get_weather(self, location_name):
        try:
            # Use Open-Meteo Geocoding API for reliable lookup
            geo_resp = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": location_name, "count": 1, "language": "en", "format": "json"},
                timeout=10,
            )
            geo = geo_resp.json()
            results = geo.get("results") or []
            if not results:
                # Fallback to geopy if geocoding API returns nothing
                location = geolocator.geocode(location_name, timeout=10)
                if not location:
                    self.speaker("Sorry, I couldn't find the location.")
                    return
                lat, lon = location.latitude, location.longitude
            else:
                lat, lon = results[0]["latitude"], results[0]["longitude"]

            url = "https://api.open-meteo.com/v1/forecast"
            wx_resp = requests.get(
                url,
                params={"latitude": lat, "longitude": lon, "current_weather": True},
                timeout=10,
            )
            data = wx_resp.json()

            current = data.get("current_weather") or {}
            temp = current.get("temperature")
            code = current.get("weathercode")
            if temp is None or code is None:
                self.speaker("Sorry, I couldn't fetch the weather information.")
                return
            desc = weather_codes.get(code, "unknown weather")

            self.speaker(f"The current temperature in {location_name} is {temp}°C with {desc}.")
        except Exception as e:
            print(e)
            self.speaker("Sorry, I couldn't fetch the weather information.")

    def get_news(self):
        api_key = os.getenv("news_api_key")
        if not api_key:
            self.speaker("News service is not configured.")
            self.speaker("Please set NEWS_API_KEY to enable headlines.")
            return
        url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}"
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            articles = data.get("articles", [])[:5]
            if not articles:
                self.speaker("Sorry, I couldn't find any news right now.")
                return
            self.speaker("Here are the top headlines:")
            for article in articles:
                self.speaker(article["title"])
        except Exception:
            self.speaker("Sorry, I couldn't fetch the news.")
