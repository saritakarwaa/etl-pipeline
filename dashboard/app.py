import streamlit as st
import duckdb
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(
    page_title="NYC Taxi Analytics",
    page_icon="🚕",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────
st.markdown(
    """

    .metric-label { font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: .05em; }
    .metric-val   { font-size: 28px; font-weight: 700; color: #e2e8f0; }
    .metric-delta { font-size: 13px; color: #34d399; }
    .insight-box  { background: #0c1a3a; border: 1px solid #1e3a6e; border-radius: 8px;
                    padding: .75rem 1rem; font-size: 13px; color: #93c5fd; }

""",
    unsafe_allow_html=True,
)


# ── Data loading ──────────────────────────────────────
@st.cache_data
def load_daily():
    conn = duckdb.connect("data/warehouse.duckdb", read_only=True)
    df = conn.execute("SELECT * FROM main.mart_daily_metrics ORDER BY pickup_date").df()
    conn.close()
    df["pickup_date"] = pd.to_datetime(df["pickup_date"])
    return df


@st.cache_data
def load_hourly_sample():
    """Sample of trip-level data for hour-of-day analysis."""
    conn = duckdb.connect("data/warehouse.duckdb", read_only=True)
    df = conn.execute(
        """
        SELECT pickup_hour, time_of_day, payment_method,
               AVG(fare_amount) AS avg_fare,
               COUNT(*)         AS trips
        FROM main.stg_taxi_trips
        GROUP BY pickup_hour, time_of_day, payment_method
        ORDER BY pickup_hour
    """
    ).df()
    conn.close()
    return df


df = load_daily()

# ── Header ────────────────────────────────────────────
st.title("🚕 NYC Taxi Analytics — January 2023")
st.caption(
    "End-to-end pipeline: TLC Open Data + Open-Meteo → DuckDB → dbt → Streamlit  "
    "· [GitHub](https://github.com/your-username/nyc-taxi-pipeline)"
)
st.divider()

# ── KPI row ───────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total trips", f"{df['total_trips'].sum():,.0f}")
col2.metric("Total revenue", f"${df['total_revenue'].sum():,.0f}")
col3.metric("Avg fare", f"${df['avg_fare'].mean():.2f}")
col4.metric("Avg tip", f"{df['avg_tip_pct'].mean():.1f}%")
col5.metric("Card payments", f"{df['pct_card_payments'].mean():.0f}%")

st.divider()

# ── Main insight: weather vs demand ──────────────────
st.subheader("Does bad weather increase taxi demand?")

st.markdown(
    """

  💡 Hypothesis: On rainy or snowy days, fewer people walk or take the subway — 
  so taxi demand should increase. Let's see what the data says.

""",
    unsafe_allow_html=True,
)

st.write("")

col_a, col_b = st.columns([3, 2])

with col_a:
    fig_weather = px.scatter(
        df,
        x="precipitation_mm",
        y="total_trips",
        color="weather_label",
        size="total_revenue",
        hover_data=["pickup_date", "avg_fare", "temp_avg_c"],
        title="Precipitation vs Trip Volume (bubble = revenue)",
        labels={
            "precipitation_mm": "Precipitation (mm)",
            "total_trips": "Total trips",
            "weather_label": "Weather",
        },
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig_weather.update_layout(
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_weather, use_container_width=True)

with col_b:
    bad = df[df["is_bad_weather_day"] == True]
    good = df[df["is_bad_weather_day"] == False]

    fig_box = go.Figure()
    fig_box.add_trace(
        go.Box(
            y=good["total_trips"],
            name="Fair weather",
            marker_color="#6366f1",
        )
    )
    fig_box.add_trace(
        go.Box(
            y=bad["total_trips"],
            name="Bad weather",
            marker_color="#f87171",
        )
    )
    fig_box.update_layout(
        title="Trip volume: fair vs bad weather days",
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=True,
    )
    st.plotly_chart(fig_box, use_container_width=True)

    # Show the actual answer
    avg_good = good["total_trips"].mean()
    avg_bad = bad["total_trips"].mean()
    delta = (avg_bad - avg_good) / avg_good * 100

    st.markdown(
        f"""
    
      📊 Finding:
      Fair weather: {avg_good:,.0f} avg trips/day
      Bad weather:  {avg_bad:,.0f} avg trips/day
      Difference: {delta:+.1f}%
    
    """,
        unsafe_allow_html=True,
    )

st.divider()

# ── Revenue trend ─────────────────────────────────────
st.subheader("Daily revenue & trip volume")

fig_rev = go.Figure()
fig_rev.add_trace(
    go.Bar(
        x=df["pickup_date"],
        y=df["total_revenue"],
        name="Revenue ($)",
        marker_color=df["is_bad_weather_day"].map({True: "#f87171", False: "#6366f1"}),
        opacity=0.85,
    )
)
fig_rev.add_trace(
    go.Scatter(
        x=df["pickup_date"],
        y=df["total_trips"],
        name="Trips",
        yaxis="y2",
        line=dict(color="#fcd34d", width=2),
        mode="lines+markers",
    )
)
fig_rev.update_layout(
    template="plotly_dark",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    yaxis=dict(title="Revenue ($)"),
    yaxis2=dict(title="Trips", overlaying="y", side="right"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    hovermode="x unified",
)
st.plotly_chart(fig_rev, use_container_width=True)
st.caption("Red bars = bad weather days (heavy rain or snow)")

st.divider()

# ── Time of day & payment ─────────────────────────────
col_c, col_d = st.columns(2)

with col_c:
    tod = df[["morning_rush_trips", "evening_rush_trips", "night_trips"]].mean()
    tod.index = [
        "Morning rush\n(6–9am)",
        "Evening rush\n(4–7pm)",
        "Night\n(8pm–midnight)",
    ]
    fig_tod = px.bar(
        x=tod.index,
        y=tod.values,
        title="Avg daily trips by time of day",
        labels={"x": "Period", "y": "Avg trips"},
        color=tod.values,
        color_continuous_scale="purples",
    )
    fig_tod.update_layout(
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig_tod, use_container_width=True)

with col_d:
    fig_card = px.area(
        df,
        x="pickup_date",
        y="pct_card_payments",
        title="Card payment adoption over January",
        labels={"pct_card_payments": "% card payments", "pickup_date": "Date"},
        color_discrete_sequence=["#6366f1"],
    )
    fig_card.update_traces(fill="tozeroy", opacity=0.7)
    fig_card.update_layout(
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_card, use_container_width=True)

st.divider()

# ── Raw data explorer ─────────────────────────────────
with st.expander("📋 View mart_daily_metrics table"):
    st.dataframe(
        df.style.format(
            {
                "total_revenue": "${:,.0f}",
                "avg_fare": "${:.2f}",
                "avg_tip_pct": "{:.1f}%",
                "pct_card_payments": "{:.1f}%",
                "temp_avg_c": "{:.1f}°C",
            }
        ),
        use_container_width=True,
    )

st.caption(
    "Data: NYC TLC Open Data + Open-Meteo · Pipeline built with Python, DuckDB, dbt Core, Streamlit"
)
