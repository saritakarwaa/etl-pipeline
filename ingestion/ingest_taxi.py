import requests
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s"
)
logger = logging.getLogger(__name__)

# NYC TLC public data — yellow taxi, January 2023
# Change the month/year to pull different periods
TAXI_URLS = {
    "2023-01": "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-01.parquet",
    "2023-02": "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-02.parquet",
    "2023-03": "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-03.parquet",
}

DATA_DIR = Path("data/raw")


def download_parquet(url: str, output_path: Path) -> Path:
    """Stream a parquet file from URL to disk."""
    if output_path.exists():
        logger.info(f"Already downloaded: {output_path.name} — skipping")
        return output_path

    logger.info(f"Downloading {output_path.name} ...")
    response = requests.get(url, stream=True, timeout=120)
    response.raise_for_status()

    total = int(response.headers.get("content-length", 0))
    downloaded = 0

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):  # 1 MB chunks
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = downloaded / total * 100
                print(f"\r  {pct:.1f}%  ({downloaded / 1e6:.1f} MB)", end="", flush=True)

    print()  # newline after progress
    logger.info(f"Saved {output_path} ({output_path.stat().st_size / 1e6:.1f} MB)")
    return output_path


def ingest_taxi(months: list[str] = None) -> list[Path]:
    """Download one or more months of taxi data."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    months = months or list(TAXI_URLS.keys())
    paths = []

    for month in months:
        if month not in TAXI_URLS:
            logger.warning(f"Unknown month key: {month}, skipping")
            continue
        url = TAXI_URLS[month]
        dest = DATA_DIR / f"yellow_taxi_{month}.parquet"
        paths.append(download_parquet(url, dest))

    return paths


if __name__ == "__main__":
    # Download just January 2023 to start
    files = ingest_taxi(months=["2023-01"])
    print(f"\n✓ Downloaded {len(files)} file(s)")
