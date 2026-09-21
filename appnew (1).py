import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Toronto Ferry Analytics",
    page_icon="⛴️",
    layout="wide"
)


# ============================================================
# TITLE
# ============================================================

st.title("⛴️ Toronto Ferry Ticket Sales & Redemption Analytics")

st.markdown(
    """
    **Toronto Island Park Ferry Operations Dashboard**

    This dashboard analyzes ticket sales, ticket redemptions,
    passenger movement, peak demand periods, and seasonal trends.
    """
)


# ============================================================
# LOAD DATASET
# ============================================================

@st.cache_data
def load_data():

    try:
        df = pd.read_csv("cleaned_toronto_ferry_data.csv")
    except FileNotFoundError:
        df = pd.read_csv("ferry_data.csv")

    # Convert timestamp
    df["Timestamp"] = pd.to_datetime(
        df["Timestamp"],
        errors="coerce"
    )

    # Remove invalid timestamps
    df = df.dropna(subset=["Timestamp"])

    # Sort chronologically
    df = df.sort_values("Timestamp")

    # Create features if they don't already exist

    if "Hour" not in df.columns:
        df["Hour"] = df["Timestamp"].dt.hour

    if "Day" not in df.columns:
        df["Day"] = df["Timestamp"].dt.day

    if "DayOfWeek" not in df.columns:
        df["DayOfWeek"] = df["Timestamp"].dt.day_name()

    if "Month" not in df.columns:
        df["Month"] = df["Timestamp"].dt.month

    if "MonthName" not in df.columns:
        df["MonthName"] = df["Timestamp"].dt.month_name()

    if "Year" not in df.columns:
        df["Year"] = df["Timestamp"].dt.year

    if "DayType" not in df.columns:
        df["DayType"] = df["Timestamp"].dt.dayofweek.apply(
            lambda x: "Weekend" if x >= 5 else "Weekday"
        )

    if "Net Movement" not in df.columns:
        df["Net Movement"] = (
            df["Tickets Sold"] -
            df["Redemption Count"]
        )

    return df


df = load_data()


# ============================================================
# CHECK DATASET
# ============================================================

if df.empty:

    st.error("The dataset is empty.")

    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("🔎 Dashboard Filters")


# ------------------------------------------------------------
# DATE FILTER
# ------------------------------------------------------------

min_date = df["Timestamp"].min().date()
max_date = df["Timestamp"].max().date()

start_date = st.sidebar.date_input(
    "Start Date",
    value=min_date,
    min_value=min_date,
    max_value=max_date
)

end_date = st.sidebar.date_input(
    "End Date",
    value=max_date,
    min_value=min_date,
    max_value=max_date
)


# ------------------------------------------------------------
# YEAR FILTER
# ------------------------------------------------------------

years = sorted(df["Year"].unique())

selected_years = st.sidebar.multiselect(
    "Select Year",
    years,
    default=years
)


# ------------------------------------------------------------
# DAY TYPE FILTER
# ------------------------------------------------------------

day_types = sorted(df["DayType"].unique())

selected_day_types = st.sidebar.multiselect(
    "Day Type",
    day_types,
    default=day_types
)


# ------------------------------------------------------------
# HOUR FILTER
# ------------------------------------------------------------

hour_range = st.sidebar.slider(
    "Hour Range",
    min_value=0,
    max_value=23,
    value=(0, 23)
)


# ============================================================
# APPLY FILTERS
# ============================================================

filtered_df = df[
    (df["Timestamp"].dt.date >= start_date) &
    (df["Timestamp"].dt.date <= end_date) &
    (df["Year"].isin(selected_years)) &
    (df["DayType"].isin(selected_day_types)) &
    (df["Hour"] >= hour_range[0]) &
    (df["Hour"] <= hour_range[1])
].copy()


# ============================================================
# CHECK FILTER RESULT
# ============================================================

if filtered_df.empty:

    st.warning(
        "No data available for the selected filters. "
        "Please change the filters."
    )

    st.stop()


# ============================================================
# KPI CALCULATIONS
# ============================================================

total_sales = filtered_df["Tickets Sold"].sum()

total_redemptions = filtered_df["Redemption Count"].sum()

net_movement = filtered_df["Net Movement"].sum()


hourly_sales = (
    filtered_df
    .groupby("Hour")["Tickets Sold"]
    .sum()
)

hourly_redemptions = (
    filtered_df
    .groupby("Hour")["Redemption Count"]
    .sum()
)


peak_sales_hour = hourly_sales.idxmax()

peak_sales_value = hourly_sales.max()


peak_redemption_hour = hourly_redemptions.idxmax()

peak_redemption_value = hourly_redemptions.max()


# ============================================================
# KPI CARDS
# ============================================================

st.subheader("📊 Key Performance Indicators")


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "🎟️ Total Tickets Sold",
        f"{total_sales:,.0f}"
    )


with col2:

    st.metric(
        "✅ Total Tickets Redeemed",
        f"{total_redemptions:,.0f}"
    )


with col3:

    st.metric(
        "👥 Net Passenger Movement",
        f"{net_movement:,.0f}"
    )


with col4:

    st.metric(
        "🔥 Peak Sales Hour",
        f"{peak_sales_hour:02d}:00"
    )


st.divider()


# ============================================================
# DATASET INFORMATION
# ============================================================

st.subheader("📋 Dataset Overview")


info_col1, info_col2, info_col3 = st.columns(3)


with info_col1:

    st.metric(
        "Records",
        f"{len(filtered_df):,}"
    )


with info_col2:

    st.metric(
        "Start Date",
        str(filtered_df["Timestamp"].min().date())
    )


with info_col3:

    st.metric(
        "End Date",
        str(filtered_df["Timestamp"].max().date())
    )


# ============================================================
# TICKET SALES OVER TIME
# ============================================================

st.subheader("📈 Ticket Sales Over Time")


daily_sales = (
    filtered_df
    .set_index("Timestamp")
    .resample("D")["Tickets Sold"]
    .sum()
    .reset_index()
)


fig_daily = px.line(
    daily_sales,
    x="Timestamp",
    y="Tickets Sold",
    title="Daily Ticket Sales"
)


fig_daily.update_layout(
    xaxis_title="Date",
    yaxis_title="Tickets Sold"
)


st.plotly_chart(
    fig_daily,
    use_container_width=True
)


# ============================================================
# SALES VS REDEMPTIONS
# ============================================================

st.subheader("🎟️ Ticket Sales vs Redemptions")


hourly_comparison = (
    filtered_df
    .groupby("Hour")[
        ["Tickets Sold", "Redemption Count"]
    ]
    .sum()
    .reset_index()
)


fig_comparison = go.Figure()


fig_comparison.add_trace(
    go.Scatter(
        x=hourly_comparison["Hour"],
        y=hourly_comparison["Tickets Sold"],
        mode="lines+markers",
        name="Tickets Sold"
    )
)


fig_comparison.add_trace(
    go.Scatter(
        x=hourly_comparison["Hour"],
        y=hourly_comparison["Redemption Count"],
        mode="lines+markers",
        name="Redemptions"
    )
)


fig_comparison.update_layout(
    title="Hourly Ticket Sales vs Redemptions",
    xaxis_title="Hour of Day",
    yaxis_title="Count"
)


st.plotly_chart(
    fig_comparison,
    use_container_width=True
)


# ============================================================
# TWO COLUMN SECTION
# ============================================================

col1, col2 = st.columns(2)


# ============================================================
# HOURLY DEMAND
# ============================================================

with col1:

    st.subheader("🕐 Demand by Hour")

    hourly_data = (
        filtered_df
        .groupby("Hour")["Tickets Sold"]
        .sum()
        .reset_index()
    )


    fig_hour = px.bar(
        hourly_data,
        x="Hour",
        y="Tickets Sold",
        title="Ticket Sales by Hour"
    )


    fig_hour.update_layout(
        xaxis_title="Hour",
        yaxis_title="Tickets Sold"
    )


    st.plotly_chart(
        fig_hour,
        use_container_width=True
    )


# ============================================================
# DAY TYPE
# ============================================================

with col2:

    st.subheader("📅 Weekday vs Weekend")

    day_type_data = (
        filtered_df
        .groupby("DayType")["Tickets Sold"]
        .sum()
        .reset_index()
    )


    fig_daytype = px.bar(
        day_type_data,
        x="DayType",
        y="Tickets Sold",
        title="Ticket Sales: Weekday vs Weekend"
    )


    fig_daytype.update_layout(
        xaxis_title="Day Type",
        yaxis_title="Tickets Sold"
    )


    st.plotly_chart(
        fig_daytype,
        use_container_width=True
    )


# ============================================================
# MONTHLY TREND
# ============================================================

st.subheader("📅 Monthly Ticket Sales")


monthly_data = (
    filtered_df
    .groupby("Month")["Tickets Sold"]
    .sum()
    .reset_index()
)


fig_month = px.bar(
    monthly_data,
    x="Month",
    y="Tickets Sold",
    title="Ticket Sales by Month"
)


fig_month.update_layout(
    xaxis_title="Month",
    yaxis_title="Tickets Sold"
)


st.plotly_chart(
    fig_month,
    use_container_width=True
)


# ============================================================
# YEARLY TREND
# ============================================================

st.subheader("📆 Yearly Ticket Sales")


yearly_data = (
    filtered_df
    .groupby("Year")["Tickets Sold"]
    .sum()
    .reset_index()
)


fig_year = px.line(
    yearly_data,
    x="Year",
    y="Tickets Sold",
    markers=True,
    title="Yearly Ticket Sales Trend"
)


fig_year.update_layout(
    xaxis_title="Year",
    yaxis_title="Tickets Sold"
)


st.plotly_chart(
    fig_year,
    use_container_width=True
)


# ============================================================
# DAY OF WEEK ANALYSIS
# ============================================================

st.subheader("🗓️ Ticket Sales by Day of Week")


day_order = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
]


day_data = (
    filtered_df
    .groupby("DayOfWeek")["Tickets Sold"]
    .sum()
    .reindex(day_order)
    .reset_index()
)


fig_day = px.bar(
    day_data,
    x="DayOfWeek",
    y="Tickets Sold",
    title="Ticket Sales by Day of Week"
)


fig_day.update_layout(
    xaxis_title="Day",
    yaxis_title="Tickets Sold"
)


st.plotly_chart(
    fig_day,
    use_container_width=True
)


# ============================================================
# HEATMAP
# ============================================================

st.subheader("🔥 Demand Heatmap")


heatmap_data = filtered_df.pivot_table(
    values="Tickets Sold",
    index="DayOfWeek",
    columns="Hour",
    aggfunc="sum"
)


heatmap_data = heatmap_data.reindex(day_order)


fig_heatmap = px.imshow(
    heatmap_data,
    labels={
        "x": "Hour",
        "y": "Day",
        "color": "Tickets Sold"
    },
    title="Ticket Sales by Day and Hour",
    aspect="auto"
)


st.plotly_chart(
    fig_heatmap,
    use_container_width=True
)


# ============================================================
# NET PASSENGER MOVEMENT
# ============================================================

st.subheader("👥 Net Passenger Movement")


net_hourly = (
    filtered_df
    .groupby("Hour")["Net Movement"]
    .sum()
    .reset_index()
)


fig_net = px.bar(
    net_hourly,
    x="Hour",
    y="Net Movement",
    title="Net Passenger Movement by Hour"
)


fig_net.update_layout(
    xaxis_title="Hour",
    yaxis_title="Net Movement"
)


st.plotly_chart(
    fig_net,
    use_container_width=True
)


# ============================================================
# PEAK AND OFF-PEAK ANALYSIS
# ============================================================

st.subheader("🚦 Peak vs Off-Peak Analysis")


peak_hour = hourly_sales.idxmax()

off_peak_hour = hourly_sales.idxmin()

peak_value = hourly_sales.max()

off_peak_value = hourly_sales.min()


peak_col1, peak_col2, peak_col3, peak_col4 = st.columns(4)


with peak_col1:

    st.metric(
        "Peak Hour",
        f"{peak_hour:02d}:00"
    )


with peak_col2:

    st.metric(
        "Peak Sales",
        f"{peak_value:,.0f}"
    )


with peak_col3:

    st.metric(
        "Off-Peak Hour",
        f"{off_peak_hour:02d}:00"
    )


with peak_col4:

    st.metric(
        "Off-Peak Sales",
        f"{off_peak_value:,.0f}"
    )


# ============================================================
# TOP 5 BUSIEST HOURS
# ============================================================

st.subheader("🏆 Busiest Hours")


top_5_hours = (
    hourly_sales
    .sort_values(ascending=False)
    .head(5)
    .reset_index()
)


top_5_hours.columns = [
    "Hour",
    "Tickets Sold"
]


st.dataframe(
    top_5_hours,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# TOP 5 OFF-PEAK HOURS
# ============================================================

st.subheader("🌙 Off-Peak Hours")


bottom_5_hours = (
    hourly_sales
    .sort_values(ascending=True)
    .head(5)
    .reset_index()
)


bottom_5_hours.columns = [
    "Hour",
    "Tickets Sold"
]


st.dataframe(
    bottom_5_hours,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# ROLLING AVERAGE
# ============================================================

st.subheader("📈 Rolling Average Analysis")


rolling_df = filtered_df.copy()

rolling_df = rolling_df.sort_values("Timestamp")


rolling_df["1H Rolling Average"] = (
    rolling_df["Tickets Sold"]
    .rolling(4)
    .mean()
)


rolling_df["4H Rolling Average"] = (
    rolling_df["Tickets Sold"]
    .rolling(16)
    .mean()
)


fig_rolling = go.Figure()


fig_rolling.add_trace(
    go.Scatter(
        x=rolling_df["Timestamp"],
        y=rolling_df["1H Rolling Average"],
        mode="lines",
        name="1-Hour Rolling Average"
    )
)


fig_rolling.add_trace(
    go.Scatter(
        x=rolling_df["Timestamp"],
        y=rolling_df["4H Rolling Average"],
        mode="lines",
        name="4-Hour Rolling Average"
    )
)


fig_rolling.update_layout(
    title="Ticket Sales Rolling Average",
    xaxis_title="Timestamp",
    yaxis_title="Average Tickets Sold"
)


st.plotly_chart(
    fig_rolling,
    use_container_width=True
)


# ============================================================
# DATA TABLE
# ============================================================

st.subheader("📋 Filtered Dataset")


st.dataframe(
    filtered_df,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# DOWNLOAD FILTERED DATA
# ============================================================

csv_data = filtered_df.to_csv(index=False)


st.download_button(
    label="⬇️ Download Filtered Data",
    data=csv_data,
    file_name="filtered_toronto_ferry_data.csv",
    mime="text/csv"
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Toronto Ferry Ticket Sales & Redemption Analytics | "
    "Data Analytics Project"
)