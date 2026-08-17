import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import pandas as pd
import plotly.express as px

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Afficionado Coffee Roasters",
    page_icon="☕",
    layout="wide"
)

# =========================================================
# TITLE
# =========================================================

st.title("☕ Afficionado Coffee Roasters")
st.subheader("Sales Trend and Time-Based Performance Analysis")

st.write(
    "Interactive dashboard for analyzing coffee sales, "
    "store performance, product performance and peak sales hours."
)

# =========================================================
# LOAD EXCEL DATA
# =========================================================

@st.cache_data
def load_data():

    import os
    import glob

    # Find Excel files in the same folder as app.py
    app_folder = os.path.dirname(os.path.abspath(__file__))

    excel_files = glob.glob(
        os.path.join(app_folder, "*.xlsx")
    )

    if not excel_files:
        st.error(
            "❌ Excel file not found. "
            "Please place the Excel file in the same folder as app.py."
        )
        st.stop()

    # Automatically select the Excel file
    file_path = excel_files[0]

    # Check available sheets
    excel_file = pd.ExcelFile(file_path)

    # Use Transactions sheet if available
    if "Transactions" in excel_file.sheet_names:
        sheet_name = "Transactions"
    else:
        sheet_name = excel_file.sheet_names[0]

    df = pd.read_excel(
        file_path,
        sheet_name=sheet_name
    )

    return df

df = load_data()

# =========================================================
# DATA PREPARATION
# =========================================================

df["transaction_time"] = pd.to_datetime(
    df["transaction_time"].astype(str),
    format="%H:%M:%S",
    errors="coerce"
)

df["hour"] = df["transaction_time"].dt.hour

df["revenue"] = (
    df["transaction_qty"] *
    df["unit_price"]
)

# =========================================================
# CREATE TIME BUCKET
# =========================================================

def create_time_bucket(hour):

    if 6 <= hour < 12:
        return "Morning"

    elif 12 <= hour < 17:
        return "Afternoon"

    elif 17 <= hour < 21:
        return "Evening"

    else:
        return "Late Hours"


df["time_bucket"] = df["hour"].apply(
    create_time_bucket
)

# =========================================================
# SIDEBAR FILTERS
# =========================================================

st.sidebar.header("🔎 Filters")

# Store filter

store_options = sorted(
    df["store_location"].dropna().unique()
)

selected_stores = st.sidebar.multiselect(
    "Store Location",
    store_options,
    default=store_options
)

# Product category filter

category_options = sorted(
    df["product_category"].dropna().unique()
)

selected_categories = st.sidebar.multiselect(
    "Product Category",
    category_options,
    default=category_options
)

# Time bucket filter

bucket_options = [
    "Morning",
    "Afternoon",
    "Evening",
    "Late Hours"
]

selected_buckets = st.sidebar.multiselect(
    "Time Bucket",
    bucket_options,
    default=bucket_options
)

# Hour range

selected_hour = st.sidebar.slider(
    "Hour Range",
    min_value=int(df["hour"].min()),
    max_value=int(df["hour"].max()),
    value=(
        int(df["hour"].min()),
        int(df["hour"].max())
    )
)

# =========================================================
# APPLY FILTERS
# =========================================================

filtered_df = df[
    (df["store_location"].isin(selected_stores))
    &
    (df["product_category"].isin(selected_categories))
    &
    (df["time_bucket"].isin(selected_buckets))
    &
    (df["hour"].between(
        selected_hour[0],
        selected_hour[1]
    ))
].copy()

# =========================================================
# KPI CALCULATIONS
# =========================================================

total_revenue = filtered_df["revenue"].sum()

total_transactions = filtered_df[
    "transaction_id"
].nunique()

total_quantity = filtered_df[
    "transaction_qty"
].sum()

average_transaction_value = (
    total_revenue /
    total_transactions
    if total_transactions > 0
    else 0
)

average_unit_price = filtered_df[
    "unit_price"
].mean()

# =========================================================
# KPI CARDS
# =========================================================

st.markdown("## 📊 Key Performance Indicators")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "Total Revenue",
        f"${total_revenue:,.2f}"
    )

with col2:
    st.metric(
        "Total Transactions",
        f"{total_transactions:,}"
    )

with col3:
    st.metric(
        "Quantity Sold",
        f"{total_quantity:,.0f}"
    )

with col4:
    st.metric(
        "Average Transaction Value",
        f"${average_transaction_value:,.2f}"
    )

with col5:
    st.metric(
        "Average Unit Price",
        f"${average_unit_price:,.2f}"
    )

st.divider()

# =========================================================
# CHECK EMPTY DATA
# =========================================================

if filtered_df.empty:

    st.warning(
        "No data available for the selected filters."
    )

    st.stop()

# =========================================================
# OVERALL SALES TREND
# =========================================================

st.header("📈 Overall Sales Trend")

hourly_sales = (
    filtered_df
    .groupby("hour")
    .agg(
        Revenue=("revenue", "sum"),
        Quantity=("transaction_qty", "sum"),
        Transactions=("transaction_id", "nunique")
    )
    .reset_index()
)

metric = st.radio(
    "Select Metric",
    [
        "Revenue",
        "Quantity",
        "Transactions"
    ],
    horizontal=True
)

fig = px.line(
    hourly_sales,
    x="hour",
    y=metric,
    markers=True,
    title=f"Hourly {metric} Trend"
)

fig.update_layout(
    xaxis_title="Hour of Day",
    yaxis_title=metric,
    xaxis=dict(dtick=1)
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# =========================================================
# TIME BUCKET ANALYSIS
# =========================================================

st.header("⏰ Sales Performance by Time Bucket")

time_bucket_sales = (
    filtered_df
    .groupby("time_bucket")
    .agg(
        Revenue=("revenue", "sum"),
        Quantity=("transaction_qty", "sum"),
        Transactions=("transaction_id", "nunique")
    )
    .reset_index()
)

bucket_order = [
    "Morning",
    "Afternoon",
    "Evening",
    "Late Hours"
]

time_bucket_sales["order"] = (
    time_bucket_sales["time_bucket"]
    .map(
        {
            "Morning": 1,
            "Afternoon": 2,
            "Evening": 3,
            "Late Hours": 4
        }
    )
)

time_bucket_sales = (
    time_bucket_sales
    .sort_values("order")
)

col1, col2 = st.columns(2)

with col1:

    fig_bucket = px.bar(
        time_bucket_sales,
        x="time_bucket",
        y="Revenue",
        text_auto=".2s",
        title="Revenue by Time Bucket"
    )

    st.plotly_chart(
        fig_bucket,
        use_container_width=True
    )

with col2:

    fig_bucket_qty = px.bar(
        time_bucket_sales,
        x="time_bucket",
        y="Quantity",
        text_auto=True,
        title="Quantity Sold by Time Bucket"
    )

    st.plotly_chart(
        fig_bucket_qty,
        use_container_width=True
    )

# =========================================================
# PEAK HOUR ANALYSIS
# =========================================================

st.header("🔥 Peak Hour Analysis")

peak_hour = (
    hourly_sales
    .sort_values(
        "Transactions",
        ascending=False
    )
    .iloc[0]
)

lowest_hour = (
    hourly_sales
    .sort_values(
        "Transactions",
        ascending=True
    )
    .iloc[0]
)

col1, col2 = st.columns(2)

with col1:

    st.success(
        f"🔥 Peak Hour: "
        f"{int(peak_hour['hour']):02d}:00\n\n"
        f"Transactions: "
        f"{int(peak_hour['Transactions']):,}\n\n"
        f"Revenue: "
        f"${peak_hour['Revenue']:,.2f}"
    )

with col2:

    st.info(
        f"🕒 Lowest Activity Hour: "
        f"{int(lowest_hour['hour']):02d}:00\n\n"
        f"Transactions: "
        f"{int(lowest_hour['Transactions']):,}"
    )

# =========================================================
# HOURLY DEMAND HEATMAP
# =========================================================

st.header("🔥 Hourly Demand Heatmap")

heatmap_data = (
    filtered_df
    .groupby(
        [
            "store_location",
            "hour"
        ]
    )
    .size()
    .reset_index(
        name="Transactions"
    )
)

heatmap = heatmap_data.pivot(
    index="store_location",
    columns="hour",
    values="Transactions"
).fillna(0)

fig_heatmap = px.imshow(
    heatmap,
    aspect="auto",
    title="Transaction Volume by Store and Hour",
    labels={
        "x": "Hour",
        "y": "Store Location",
        "color": "Transactions"
    }
)

st.plotly_chart(
    fig_heatmap,
    use_container_width=True
)

# =========================================================
# STORE PERFORMANCE
# =========================================================

st.header("🏪 Store Performance Comparison")

store_sales = (
    filtered_df
    .groupby("store_location")
    .agg(
        Revenue=("revenue", "sum"),
        Transactions=("transaction_id", "nunique"),
        Quantity=("transaction_qty", "sum")
    )
    .reset_index()
    .sort_values(
        "Revenue",
        ascending=False
    )
)

col1, col2 = st.columns(2)

with col1:

    fig_store = px.bar(
        store_sales,
        x="store_location",
        y="Revenue",
        text_auto=".2s",
        title="Revenue by Store Location"
    )

    st.plotly_chart(
        fig_store,
        use_container_width=True
    )

with col2:

    fig_store_transactions = px.bar(
        store_sales,
        x="store_location",
        y="Transactions",
        text_auto=True,
        title="Transactions by Store Location"
    )

    st.plotly_chart(
        fig_store_transactions,
        use_container_width=True
    )

st.dataframe(
    store_sales,
    use_container_width=True,
    hide_index=True
)

# =========================================================
# STORE AND TIME BUCKET
# =========================================================

st.header("🏪 Store Performance by Time Bucket")

store_bucket = (
    filtered_df
    .groupby(
        [
            "store_location",
            "time_bucket"
        ]
    )["revenue"]
    .sum()
    .reset_index()
)

fig_store_bucket = px.bar(
    store_bucket,
    x="store_location",
    y="revenue",
    color="time_bucket",
    barmode="group",
    title="Store Revenue by Time Bucket"
)

st.plotly_chart(
    fig_store_bucket,
    use_container_width=True
)

# =========================================================
# PRODUCT CATEGORY ANALYSIS
# =========================================================

st.header("☕ Product Category Performance")

category_sales = (
    filtered_df
    .groupby("product_category")
    .agg(
        Revenue=("revenue", "sum"),
        Quantity=("transaction_qty", "sum"),
        Transactions=("transaction_id", "nunique")
    )
    .reset_index()
    .sort_values(
        "Revenue",
        ascending=False
    )
)

col1, col2 = st.columns(2)

with col1:

    fig_category = px.bar(
        category_sales,
        x="product_category",
        y="Revenue",
        text_auto=".2s",
        title="Revenue by Product Category"
    )

    st.plotly_chart(
        fig_category,
        use_container_width=True
    )

with col2:

    fig_category_qty = px.bar(
        category_sales,
        x="product_category",
        y="Quantity",
        text_auto=True,
        title="Quantity Sold by Product Category"
    )

    st.plotly_chart(
        fig_category_qty,
        use_container_width=True
    )

# =========================================================
# TOP 10 PRODUCT TYPES
# =========================================================

st.header("🏆 Top 10 Product Types")

top_products = (
    filtered_df
    .groupby("product_type")
    .agg(
        Revenue=("revenue", "sum"),
        Quantity=("transaction_qty", "sum")
    )
    .reset_index()
    .sort_values(
        "Revenue",
        ascending=False
    )
    .head(10)
)

fig_products = px.bar(
    top_products.sort_values(
        "Revenue"
    ),
    x="Revenue",
    y="product_type",
    orientation="h",
    text_auto=".2s",
    title="Top 10 Product Types by Revenue"
)

st.plotly_chart(
    fig_products,
    use_container_width=True
)

# =========================================================
# PRODUCT DETAIL ANALYSIS
# =========================================================

st.header("📦 Product Detail Performance")

product_details = (
    filtered_df
    .groupby(
        [
            "product_category",
            "product_type",
            "product_detail"
        ]
    )
    .agg(
        Revenue=("revenue", "sum"),
        Quantity=("transaction_qty", "sum"),
        Transactions=("transaction_id", "nunique")
    )
    .reset_index()
    .sort_values(
        "Revenue",
        ascending=False
    )
    .head(20)
)

st.dataframe(
    product_details,
    use_container_width=True,
    hide_index=True
)

# =========================================================
# BUSINESS INSIGHTS
# =========================================================

st.header("💡 Key Business Insights")

top_store = store_sales.iloc[0]

top_category = category_sales.iloc[0]

top_time_bucket = (
    time_bucket_sales
    .sort_values(
        "Revenue",
        ascending=False
    )
    .iloc[0]
)

top_product = top_products.iloc[0]

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.info(
        f"🏪 **Top Store**\n\n"
        f"{top_store['store_location']}\n\n"
        f"Revenue: ${top_store['Revenue']:,.2f}"
    )

with col2:

    st.info(
        f"☕ **Top Category**\n\n"
        f"{top_category['product_category']}\n\n"
        f"Revenue: ${top_category['Revenue']:,.2f}"
    )

with col3:

    st.info(
        f"⏰ **Best Time Bucket**\n\n"
        f"{top_time_bucket['time_bucket']}\n\n"
        f"Revenue: ${top_time_bucket['Revenue']:,.2f}"
    )

with col4:

    st.info(
        f"🏆 **Top Product Type**\n\n"
        f"{top_product['product_type']}\n\n"
        f"Revenue: ${top_product['Revenue']:,.2f}"
    )

# =========================================================
# RECOMMENDATIONS
# =========================================================

st.header("📌 Business Recommendations")

st.write(
    f"• **Staffing:** Increase staffing during the peak "
    f"hour around {int(peak_hour['hour']):02d}:00."
)

st.write(
    f"• **Store Management:** Use "
    f"{top_store['store_location']} as a benchmark "
    f"for store performance."
)

st.write(
    f"• **Product Planning:** Maintain sufficient inventory "
    f"for high-performing product categories and product types."
)

st.write(
    f"• **Time-Based Planning:** Align staffing and inventory "
    f"with the strongest performing time buckets."
)

st.write(
    "• **Performance Monitoring:** Regularly monitor revenue, "
    "transactions and quantity sold to identify changes in demand."
)

# =========================================================
# DATA QUALITY
# =========================================================

st.header("🔍 Data Quality Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Rows",
        f"{len(df):,}"
    )

with col2:
    st.metric(
        "Columns",
        df.shape[1]
    )

with col3:
    st.metric(
        "Missing Values",
        int(df.isna().sum().sum())
    )

with col4:
    st.metric(
        "Duplicate Rows",
        int(df.duplicated().sum())
    )

# =========================================================
# DATA PREVIEW
# =========================================================

with st.expander("📋 View Filtered Data"):

    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True
    )

# =========================================================
# DOWNLOAD
# =========================================================

csv_file = filtered_df.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    "⬇️ Download Filtered Data",
    data=csv_file,
    file_name="coffee_sales_filtered.csv",
    mime="text/csv"
)

# =========================================================
# NOTE
# =========================================================

st.divider()

st.caption(
    "Note: The supplied Afficionado Coffee Roasters dataset "
    "contains transaction time and hour information but does "
    "not contain a calendar date/day-of-week field. Therefore, "
    "day-of-week analysis is not fabricated. The dashboard "
    "focuses on the available time-based, store and product data."
)

st.caption(
    "Afficionado Coffee Roasters | "
    "Python • Pandas • Plotly • Streamlit"
)
