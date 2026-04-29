import httpx
import csv
import urllib.request
from pathlib import Path
from typing import Dict, Any, Optional

CITY_LIST_URL = "https://raw.githubusercontent.com/qwd/LocationList/master/China-City-List-latest.csv"
CITY_LIST_FILE = Path(__file__).parent.parent / "data" / "city_list.csv"

class WeatherService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self._city_cache: Dict[str, str] = {}  # name -> location_id

    def download_city_list(self) -> bool:
        """Download city list from GitHub and save to local file."""
        try:
            with urllib.request.urlopen(CITY_LIST_URL) as response:
                content = response.read().decode('utf-8')
            CITY_LIST_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CITY_LIST_FILE, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Failed to download city list: {e}")
            return False

    def _load_city_list(self) -> Dict[str, str]:
        """Load city list from local CSV file."""
        if self._city_cache:
            return self._city_cache

        if not CITY_LIST_FILE.exists():
            print(f"City list not found at {CITY_LIST_FILE}, please run download first")
            return self._city_cache

        try:
            with open(CITY_LIST_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()

            reader = csv.reader(lines)
            next(reader, None)  # skip header row
            next(reader, None)  # skip version row

            for row in reader:
                if len(row) >= 3:
                    location_id = row[0]
                    name_en = row[1].lower()
                    name_zh = row[2]
                    self._city_cache[name_en] = location_id
                    self._city_cache[name_zh] = location_id
        except Exception as e:
            print(f"Failed to load city list: {e}")

        return self._city_cache

    def get_location_id(self, city_name: str) -> Optional[str]:
        """Convert city name to QWeather location ID."""
        cache = self._load_city_list()

        # Direct lookup (case-insensitive for English)
        name_lower = city_name.lower()
        if name_lower in cache:
            return cache[name_lower]

        # Try partial match for Chinese
        for name, loc_id in cache.items():
            if city_name in name or name in city_name:
                return loc_id

        return None

    async def get_weather(self, location: str, api_key: str, api_host: str = "devapi.qweather.com", is_tomorrow: bool = False) -> Dict[str, Any]:
        """
        Get weather from QWeather API.
        Args:
            location: City name (e.g., "上海" or "shanghai")
            api_key: QWeather API key
            api_host: QWeather API host
            is_tomorrow: If True, get tomorrow's forecast instead of current weather
        Returns:
            Weather data dict
        """
        # Convert city name to location ID
        location_id = self.get_location_id(location)
        if not location_id:
            return {"success": False, "error": f"未知城市: {location}"}

        if is_tomorrow:
            # Use 3-day forecast API for tomorrow
            url = f"https://{api_host}/v7/weather/3d"
            params = {
                "location": location_id,
                "key": api_key
            }
        else:
            url = f"https://{api_host}/v7/weather/now"
            params = {
                "location": location_id,
                "key": api_key
            }

        try:
            resp = await self.client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

            if data.get("code") != "200":
                return {"success": False, "error": f"API error: {data.get('code')}"}

            if is_tomorrow:
                # Get tomorrow's weather from 3-day forecast
                daily_list = data.get("daily", [])
                if len(daily_list) >= 2:
                    tomorrow = daily_list[1]  # Index 1 is tomorrow
                    return {
                        "success": True,
                        "location": data.get("location", {}).get("name", location),
                        "temp": tomorrow.get("tempMin", "N/A") + "~" + tomorrow.get("tempMax", "N/A") + "°C",
                        "condition": tomorrow.get("textDay", tomorrow.get("textNight", "Unknown")),
                        "wind": tomorrow.get("windDirDay", tomorrow.get("windDirNight", "Unknown")),
                        "humidity": tomorrow.get("humidity", "N/A"),
                    }
                return {"success": False, "error": "无法获取天气预报"}
            else:
                now = data.get("now", {})
                return {
                    "success": True,
                    "location": data.get("location", {}).get("name", location),
                    "temp": now.get("temp", "N/A"),
                    "feels_like": now.get("feelsLike", "N/A"),
                    "condition": now.get("text", "Unknown"),
                    "wind": now.get("windDir", "Unknown"),
                    "humidity": now.get("humidity", "N/A"),
                    "vis": now.get("vis", "N/A"),
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_weather_by_coord(self, lat: float, lon: float, api_key: str, api_host: str = "devapi.qweather.com") -> Dict[str, Any]:
        """
        Get current weather by coordinates.
        """
        url = f"https://{api_host}/v7/weather/now"
        params = {
            "location": f"{lon},{lat}",
            "key": api_key
        }

        try:
            resp = await self.client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

            if data.get("code") != "200":
                return {"success": False, "error": f"API error: {data.get('code')}"}

            now = data.get("now", {})
            return {
                "success": True,
                "location": data.get("location", {}).get("name", "Unknown"),
                "temp": now.get("temp", "N/A"),
                "feels_like": now.get("feelsLike", "N/A"),
                "condition": now.get("text", "Unknown"),
                "wind": now.get("windDir", "Unknown"),
                "humidity": now.get("humidity", "N/A"),
                "vis": now.get("vis", "N/A"),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def close(self):
        await self.client.aclose()