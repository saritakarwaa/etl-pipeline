import requests
import pandas as pd
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path("data/raw")

# Open-Meteo: no API key, completely free
BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

# NYC coordinates
NYC_LAT = 40.7128
NYC_LON = -74.0060


def fetch_weather(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch daily weather stats for NYC.
    start_date / end_date format: "YYYY-MM-DD"
    """
    params = {
        "latitude": NYC_LAT,
        "longitude": NYC_LON,
        "start_date": start_date,
        "end_date": end_date,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "windspeed_10m_max",
            "weathercode",        # WMO code (0=clear, 61+=rain, 71+=snow)
        ],
        "timezone": "America/New_York",
    }

    logger.info(f"Fetching NYC weather {start_date} → {end_date} from Open-Meteo")
    response = requests.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    daily = data["daily"]
    df = pd.DataFrame({
        "date":          daily["time"],
        "temp_max_c":    daily["temperature_2m_max"],
        "temp_min_c":    daily["temperature_2m_min"],
        "precipitation": daily["precipitation_sum"],
        "wind_speed":    daily["windspeed_10m_max"],
        "weather_code":  daily["weathercode"],
    })
    df["date"] = pd.to_datetime(df["date"]).dt.date

    # Derive human-readable condition
    def wmo_to_label(code):
        if code == 0:              return "Clear"
        if code in range(1, 4):    return "Partly cloudy"
        if code in range(45, 68):  return "Foggy / drizzle"
        if code in range(61, 68):  return "Rainy"
        if code in range(71, 78):  return "Snowy"
        if code >= 80:             return "Stormy"
        return "Overcast"

    df["weather_label"] = df["weather_code"].apply(wmo_to_label)
    return df


def ingest_weather(start: str = "2023-01-01", end: str = "2023-01-31") -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    df = fetch_weather(start, end)
    output_path = DATA_DIR / f"weather_nyc_{start[:7]}.parquet"
    df.to_parquet(output_path, index=False)

    logger.info(f"Saved {len(df)} rows → {output_path}")
    return output_path


if __name__ == "__main__":
    path = ingest_weather("2023-01-01", "2023-01-31")
    print(f"\n✓ Weather data saved to {path}")
