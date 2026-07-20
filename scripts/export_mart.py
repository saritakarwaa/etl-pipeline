"""
Export the mart table to a small parquet for Streamlit Cloud deployment.
The deployed app reads this parquet instead of the full DuckDB warehouse.
"""
import duckdb
import pandas as pd
from pathlib import Path

conn = duckdb.connect("data/warehouse.duckdb", read_only=True)
df = conn.execute("SELECT * FROM main.mart_daily_metrics").df()
conn.close()

# Save to dashboard/data/ — this WILL be committed to git (it's tiny ~5KB)
output = Path("dashboard/data/mart_daily_metrics.parquet")
output.parent.mkdir(exist_ok=True)
df.to_parquet(output, index=False)

print(f"✓ Exported {len(df)} rows to {output} ({output.stat().st_size / 1024:.1f} KB)")
