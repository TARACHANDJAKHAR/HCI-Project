"""
Info Processor - Handles informational queries.

Provides:
- Current time
- Current date
- Weather information (using Open-Meteo API)
- News headlines (using NewsAPI, requires API key)

This processor handles general information requests that don't require
data storage, just real-time information fetching.
"""

import datetime
import requests
from geopy.geocoders import Nominatim
from .Base_Processor import BaseProcessor
import os

# Weather code mapping from Open-Meteo API
# Maps numeric weather codes to human-readable descriptions
weather_codes = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    12: "fog",
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

# Initialize geocoder for location lookup (fallback)
# Used if Open-Meteo geocoding API fails
geolocator = Nominatim(user_agent="elderly_assistant")


class InfoProcessor(BaseProcessor):
    """
    Processor for informational queries like time, date, weather, and news.
    
    All methods fetch real-time information from external APIs or system time.
    No data is stored - just provides current information on demand.
    """
    
    # Keywords that trigger this processor
    keywords = ["time", "date", "weather", "news"]

    def handle(self, command: str):
        """
        Route command to appropriate info handler.
        
        Args:
            command (str): User's command text
        """
        if "time" in command:
            # Get current time in HH:MM:SS format
            now = datetime.datetime.now().strftime("%H:%M:%S")
            self.speaker(f"The current time is {now}")

        elif "date" in command:
            # Get current date in readable format (e.g., "January 15, 2024")
            today = datetime.date.today().strftime("%B %d, %Y")
            self.speaker(f"Today's date is {today}")

        elif "weather" in command:
            # Get weather for default location (can be made dynamic)
            # Currently hardcoded to "Surat, India" - can be made user-configurable
            self.get_weather("Surat, India")

        elif "news" in command:
            # Get top news headlines
            self.get_news()

        return True

    def get_weather(self, location_name):
        """
        Fetch current weather for a given location.
        
        Uses Open-Meteo API which is free and doesn't require API key.
        First tries Open-Meteo geocoding, falls back to geopy if needed.
        
        Args:
            location_name (str): Location name (e.g., "Surat, India", "New York")
        """
        try:
            # Step 1: Get coordinates using Open-Meteo Geocoding API
            # This is more reliable than geopy and doesn't require API key
            geo_resp = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={
                    "name": location_name,
                    "count": 1,           # Only need first result
                    "language": "en",     # English language
                    "format": "json"
                },
                timeout=10,  # 10 second timeout to avoid hanging
            )
            geo = geo_resp.json()
            results = geo.get("results") or []
            
            if not results:
                # Fallback to geopy if Open-Meteo geocoding returns nothing
                location = geolocator.geocode(location_name, timeout=10)
                if not location:
                    self.speaker("Sorry, I couldn't find the location.")
                    return
                lat, lon = location.latitude, location.longitude
            else:
                # Use coordinates from Open-Meteo
                lat, lon = results[0]["latitude"], results[0]["longitude"]

            # Step 2: Get weather data using coordinates
            url = "https://api.open-meteo.com/v1/forecast"
            wx_resp = requests.get(
                url,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current_weather": True  # Get current conditions
                },
                timeout=10,
            )
            data = wx_resp.json()

            # Step 3: Extract and format weather information
            current = data.get("current_weather") or {}
            temp = current.get("temperature")
            code = current.get("weathercode")
            
            # Validate we got the required data
            if temp is None or code is None:
                self.speaker("Sorry, I couldn't fetch the weather information.")
                return
            
            # Convert numeric weather code to description
            desc = weather_codes.get(code, "unknown weather")

            # Speak the weather information
            self.speaker(f"The current temperature in {location_name} is {temp}°C with {desc}.")
        except Exception as e:
            # Log error for debugging but provide user-friendly message
            print(e)
            self.speaker("Sorry, I couldn't fetch the weather information.")

    def get_news(self):
        """
        Fetch top news headlines from NewsAPI.
        
        Requires NEWS_API_KEY environment variable to be set.
        If not set, informs user how to configure it.
        
        Fetches top 5 headlines from US news sources.
        """
        # Get API key from environment variables
        api_key = os.getenv("news_api_key")
        
        # Check if API key is configured
        if not api_key:
            self.speaker("News service is not configured.")
            self.speaker("Please set NEWS_API_KEY to enable headlines.")
            return
        
        # Construct NewsAPI URL
        url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}"
        
        try:
            # Fetch news headlines
            response = requests.get(url, timeout=10)
            data = response.json()
            
            # Get first 5 articles
            articles = data.get("articles", [])[:5]
            
            if not articles:
                self.speaker("Sorry, I couldn't find any news right now.")
                return
            
            # Announce headlines
            self.speaker("Here are the top headlines:")
            for article in articles:
                # Speak each headline title
                self.speaker(article["title"])
        except Exception:
            # Handle any errors gracefully
            self.speaker("Sorry, I couldn't fetch the news.")
