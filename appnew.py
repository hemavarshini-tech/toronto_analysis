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

    This dashboard analyzes sales count, ticket redemptions,
    passenger movement, peak demand periods, and seasonal trends.
    """
)


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():

    file_path = "Toronto Island Ferry Tickets.xls"

    try:
        df = pd.read_csv(file_path)

    except Exception:
        try:
            df = pd.read_csv(file_path, sep="\t")

        except Exception as e:
            st.error("Unable to read the dataset.")
            st.write("Error:", e)
            st.stop()

    return df


df = load_data()


# ============================================================
# CHECK DATASET
# ============================================================

if df.empty:

    st.error("The dataset is empty.")

    st.stop()


# ============================================================
# CLEAN COLUMN NAMES
# ============================================================

df.columns = (
    df.columns
    .astype(str)
    .str.strip()
)


# ============================================================
# NORMALIZE COLUMN NAMES FOR SEARCHING
# ============================================================

normalized_columns = {
    col: (
        str(col)
        .strip()
        .lower()
        .replace("_", " ")
        .replace("-", " ")
    )
    for col in df.columns
}


# ============================================================
# FIND DATE / TIMESTAMP COLUMN
# ============================================================

date_column = None

date_keywords = [
    "timestamp",
    "date",
    "datetime",
    "date time",
    "date_time"
]

for col, normalized in normalized_columns.items():

    if any(keyword in normalized for keyword in date_keywords):

        date_column = col

        break


if date_column is None:

    st.error("No date/timestamp column was found.")

    st.write("Available columns:")

    st.write(list(df.columns))

    st.stop()


# ============================================================
# CREATE TIMESTAMP
# ============================================================

df["Timestamp"] = pd.to_datetime(
    df[date_column],
    errors="coerce"
)


df = df.dropna(
    subset=["Timestamp"]
).copy()


if df.empty:

    st.error(
        "The dataset does not contain valid date/timestamp values."
    )

    st.stop()


# ============================================================
# FIND SALES COUNT COLUMN
# ============================================================

sales_column = None

for col, normalized in normalized_columns.items():

    if "sales count" in normalized:

        sales_column = col

        break


if sales_column is None:

    st.error("Sales Count column was not found.")

    st.write("Available columns:")

    st.write(list(df.columns))

    st.stop()


# ============================================================
# CREATE STANDARD SALES COUNT COLUMN
# ============================================================

df["Sales Count"] = pd.to_numeric(
    df[sales_column],
    errors="coerce"
).fillna(0)


# ============================================================
# FIND REDEMPTION COLUMN
# ============================================================

redemption_column = None

redemption_keywords = [
    "redemption count",
    "redemptions",
    "redemption",
    "redeemed",
    "ticket redemption"
]

for col, normalized in normalized_columns.items():

    if any(keyword in normalized for keyword in redemption_keywords):

        redemption_column = col

        break


if redemption_column is None:

    st.error("Ticket redemption column was not found.")

    st.write("Available columns:")

    st.write(list(df.columns))

    st.stop()


# ============================================================
# CREATE STANDARD REDEMPTION COLUMN
# ============================================================

df["Redemption Count"] = pd.to_numeric(
    df[redemption_column],
    errors="coerce"
).fillna(0)


# ============================================================
# CREATE TIME FEATURES
# ============================================================

df["Year"] = df["Timestamp"].dt.year

df["Month"] = df["Timestamp"].dt.month

df["MonthName"] = df["Timestamp"].dt.month_name()

df["Hour"] = df["Timestamp"].dt.hour

df["Day"] = df["Timestamp"].dt.day

df["DayOfWeek"] = df["Timestamp"].dt.day_name()


# ============================================================
# CREATE DAY TYPE
# ============================================================

df["DayType"] = np.where(
    df["Timestamp"].dt.dayofweek >= 5,
    "Weekend",
    "Weekday"
)


# ============================================================
# CREATE NET MOVEMENT
# ============================================================

df["Net Movement"] = (
    df["Sales Count"]
    - df["Redemption Count"]
)


# ============================================================
# DATE RANGE
# ============================================================

min_date = df["Timestamp"].min().date()

max_date = df["Timestamp"].max().date()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("🔎 Dashboard Filters")


# ============================================================
# DATE FILTER
# ============================================================

selected_dates = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)


if isinstance(selected_dates, tuple) and len(selected_dates) == 2:

    start_date = selected_dates[0]

    end_date = selected_dates[1]

else:

    start_date = min_date

    end_date = max_date


# ============================================================
# YEAR FILTER
# ============================================================

years = sorted(
    df["Year"].dropna().unique()
)


selected_years = st.sidebar.multiselect(
    "Select Year",
    years,
    default=years
)


# ============================================================
# DAY TYPE FILTER
# ============================================================

day_types = sorted(
    df["DayType"].unique()
)


selected_day_types = st.sidebar.multiselect(
    "Select Day Type",
    day_types,
    default=day_types
)


# ============================================================
# HOUR FILTER
# ============================================================

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

total_sales = filtered_df["Sales Count"].sum()

total_redemptions = filtered_df["Redemption Count"].sum()

net_movement = filtered_df["Net Movement"].sum()


# ============================================================
# HOURLY SALES
# ============================================================

hourly_sales = (
    filtered_df
    .groupby("Hour")["Sales Count"]
    .sum()
)


# ============================================================
# HOURLY REDEMPTIONS
# ============================================================

hourly_redemptions = (
    filtered_df
    .groupby("Hour")["Redemption Count"]
    .sum()
)


# ============================================================
# PEAK SALES
# ============================================================

peak_sales_hour = hourly_sales.idxmax()

peak_sales_value = hourly_sales.max()


# ============================================================
# PEAK REDEMPTION
# ============================================================

peak_redemption_hour = hourly_redemptions.idxmax()

peak_redemption_value = hourly_redemptions.max()


# ============================================================
# KPI CARDS
# ============================================================

st.subheader("📊 Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "🎟️ Total Sales",
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
# SALES OVER TIME
# ============================================================

st.subheader("📈 Sales Over Time")


daily_sales = (
    filtered_df
    .set_index("Timestamp")
    .resample("D")["Sales Count"]
    .sum()
    .reset_index()
)


fig_daily = px.line(
    daily_sales,
    x="Timestamp",
    y="Sales Count",
    title="Daily Sales Count"
)


fig_daily.update_layout(
    xaxis_title="Date",
    yaxis_title="Sales Count"
)


st.plotly_chart(
    fig_daily,
    use_container_width=True
)


# ============================================================
# SALES VS REDEMPTIONS
# ============================================================

st.subheader("🎟️ Sales Count vs Redemptions")


hourly_comparison = (
    filtered_df
    .groupby("Hour")[
        ["Sales Count", "Redemption Count"]
    ]
    .sum()
    .reset_index()
)


fig_comparison = go.Figure()


fig_comparison.add_trace(
    go.Scatter(
        x=hourly_comparison["Hour"],
        y=hourly_comparison["Sales Count"],
        mode="lines+markers",
        name="Sales Count"
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
    title="Hourly Sales Count vs Redemptions",
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
        .groupby("Hour")["Sales Count"]
        .sum()
        .reset_index()
    )


    fig_hour = px.bar(
        hourly_data,
        x="Hour",
        y="Sales Count",
        title="Sales Count by Hour"
    )


    fig_hour.update_layout(
        xaxis_title="Hour",
        yaxis_title="Sales Count"
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
        .groupby("DayType")["Sales Count"]
        .sum()
        .reset_index()
    )


    fig_daytype = px.bar(
        day_type_data,
        x="DayType",
        y="Sales Count",
        title="Sales Count: Weekday vs Weekend"
    )


    fig_daytype.update_layout(
        xaxis_title="Day Type",
        yaxis_title="Sales Count"
    )


    st.plotly_chart(
        fig_daytype,
        use_container_width=True
    )


# ============================================================
# MONTHLY TREND
# ============================================================

st.subheader("📅 Monthly Sales Count")


monthly_data = (
    filtered_df
    .groupby("Month")["Sales Count"]
    .sum()
    .reset_index()
)


fig_month = px.bar(
    monthly_data,
    x="Month",
    y="Sales Count",
    title="Sales Count by Month"
)


fig_month.update_layout(
    xaxis_title="Month",
    yaxis_title="Sales Count"
)


st.plotly_chart(
    fig_month,
    use_container_width=True
)


# ============================================================
# YEARLY TREND
# ============================================================

st.subheader("📆 Yearly Sales Count")


yearly_data = (
    filtered_df
    .groupby("Year")["Sales Count"]
    .sum()
    .reset_index()
)


fig_year = px.line(
    yearly_data,
    x="Year",
    y="Sales Count",
    markers=True,
    title="Yearly Sales Count Trend"
)


fig_year.update_layout(
    xaxis_title="Year",
    yaxis_title="Sales Count"
)


st.plotly_chart(
    fig_year,
    use_container_width=True
)


# ============================================================
# DAY OF WEEK ANALYSIS
# ============================================================

st.subheader("🗓️ Sales Count by Day of Week")


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
    .groupby("DayOfWeek")["Sales Count"]
    .sum()
    .reindex(day_order)
    .fillna(0)
    .reset_index()
)


fig_day = px.bar(
    day_data,
    x="DayOfWeek",
    y="Sales Count",
    title="Sales Count by Day of Week"
)


fig_day.update_layout(
    xaxis_title="Day",
    yaxis_title="Sales Count"
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
    values="Sales Count",
    index="DayOfWeek",
    columns="Hour",
    aggfunc="sum",
    fill_value=0
)


heatmap_data = heatmap_data.reindex(
    day_order
)


fig_heatmap = px.imshow(
    heatmap_data,
    labels={
        "x": "Hour",
        "y": "Day",
        "color": "Sales Count"
    },
    title="Sales Count by Day and Hour",
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
        "Peak Sales Count",
        f"{peak_value:,.0f}"
    )


with peak_col3:

    st.metric(
        "Off-Peak Hour",
        f"{off_peak_hour:02d}:00"
    )


with peak_col4:

    st.metric(
        "Off-Peak Sales Count",
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
    "Sales Count"
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
    "Sales Count"
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


rolling_df = rolling_df.sort_values(
    "Timestamp"
)


rolling_df["1H Rolling Average"] = (
    rolling_df["Sales Count"]
    .rolling(4)
    .mean()
)


rolling_df["4H Rolling Average"] = (
    rolling_df["Sales Count"]
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
    title="Sales Count Rolling Average",
    xaxis_title="Timestamp",
    yaxis_title="Average Sales Count"
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

csv_data = filtered_df.to_csv(
    index=False
)


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
