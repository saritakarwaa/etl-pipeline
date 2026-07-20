import duckdb
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = "data/warehouse.duckdb"
RAW_DIR = Path("data/raw")


def get_conn():
    conn = duckdb.connect(DB_PATH)
    conn.execute("CREATE SCHEMA IF NOT EXISTS raw")
    return conn


def load_taxi(conn: duckdb.DuckDBPyConnection):
    """Load all available taxi parquet files into raw.taxi_trips."""
    parquet_files = list(RAW_DIR.glob("yellow_taxi_*.parquet"))
    if not parquet_files:
        raise FileNotFoundError("No taxi parquet files found in data/raw/")

    # DuckDB can read multiple parquet files at once with glob
    pattern = str(RAW_DIR / "yellow_taxi_*.parquet")

    conn.execute(f"""
        CREATE OR REPLACE TABLE raw.taxi_trips AS
        SELECT
            tpep_pickup_datetime,
            tpep_dropoff_datetime,
            passenger_count,
            trip_distance,
            fare_amount,
            extra,
            mta_tax,
            tip_amount,
            tolls_amount,
            improvement_surcharge,
            total_amount,
            payment_type,
            RatecodeID
        FROM read_parquet('{pattern}')
        WHERE
            passenger_count > 0
            AND trip_distance > 0
            AND fare_amount    > 0
            AND total_amount   > 0
    """)

    count = conn.execute("SELECT COUNT(*) FROM raw.taxi_trips").fetchone()[0]
    logger.info(f"Loaded {count:,} rows into raw.taxi_trips")


def load_weather(conn: duckdb.DuckDBPyConnection):
    """Load all available weather parquet files into raw.weather."""
    pattern = str(RAW_DIR / "weather_nyc_*.parquet")

    conn.execute(f"""
        CREATE OR REPLACE TABLE raw.weather AS
        SELECT * FROM read_parquet('{pattern}')
    """)

    count = conn.execute("SELECT COUNT(*) FROM raw.weather").fetchone()[0]
    logger.info(f"Loaded {count} rows into raw.weather")


def run_quality_checks(conn: duckdb.DuckDBPyConnection):
    """Simple data quality checks — surface issues before dbt runs."""
    print("\n" + "="*50)
    print("  DATA QUALITY REPORT")
    print("="*50)

    # Taxi stats
    taxi_stats = conn.execute("""
        SELECT
            COUNT(*)                               AS total_rows,
            MIN(tpep_pickup_datetime)              AS earliest_pickup,
            MAX(tpep_pickup_datetime)              AS latest_pickup,
            ROUND(MIN(fare_amount), 2)             AS min_fare,
            ROUND(MAX(fare_amount), 2)             AS max_fare,
            ROUND(AVG(fare_amount), 2)             AS avg_fare,
            ROUND(AVG(tip_amount), 2)              AS avg_tip,
            SUM(CASE WHEN payment_type = 1
                THEN 1 ELSE 0 END) * 100.0
                / COUNT(*)                         AS pct_card_payments
        FROM raw.taxi_trips
    """).df()

    print("\n📊 Taxi trips:")
    for col in taxi_stats.columns:
        print(f"   {col:<25} {taxi_stats[col].iloc[0]}")

    # Weather stats
    weather_stats = conn.execute("""
        SELECT
            COUNT(*)               AS days,
            MIN(date)              AS start_date,
            MAX(date)              AS end_date,
            ROUND(AVG(temp_max_c), 1) AS avg_high_c,
            ROUND(SUM(precipitation), 1) AS total_rain_mm
        FROM raw.weather
    """).df()

    print("\n🌤 Weather data:")
    for col in weather_stats.columns:
        print(f"   {col:<25} {weather_stats[col].iloc[0]}")

    print("\n" + "="*50)


if __name__ == "__main__":
    conn = get_conn()
    load_taxi(conn)
    load_weather(conn)
    run_quality_checks(conn)
    conn.close()
    print(f"\n✓ DuckDB warehouse ready at {DB_PATH}")
