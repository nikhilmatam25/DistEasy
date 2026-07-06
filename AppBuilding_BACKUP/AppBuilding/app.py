import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ==================================
# PAGE CONFIGURATION
# ==================================
st.set_page_config(
    page_title="LION Distributor Portal",
    page_icon="🦁",
    layout="wide"
)

# ==================================
# CUSTOM CSS STYLING
# ==================================
st.markdown("""
<style>
    /* Premium Glassmorphic Metric Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.08);
        transition: transform 0.2s ease-in-out;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    .metric-title {
        font-size: 14px;
        color: #888888;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 32px;
        font-weight: 700;
        color: #1E3A8A; /* Deep Blue */
        margin-bottom: 5px;
    }
    .metric-desc {
        font-size: 12px;
        color: #6B7280;
    }
    
    /* Dark mode support override */
    @media (prefers-color-scheme: dark) {
        .metric-value {
            color: #60A5FA; /* Light Blue */
        }
        .metric-card {
            background: rgba(17, 24, 39, 0.7);
        }
    }
    
    /* Global layout style improvements */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ==================================
# LOGIN SYSTEM
# ==================================
USERNAME = "admin"
PASSWORD = "lion123"

# Initialize session state for login
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# Sidebar status
st.sidebar.title("🦁 LION Distributor")

if not st.session_state["logged_in"]:
    # Center-aligned premium Login Form
    col_l, col_c, col_r = st.columns([1, 1.5, 1])
    with col_c:
        st.markdown("<h2 style='text-align: center;'>Distributor System Login</h2>", unsafe_allow_html=True)
        login_container = st.container(border=True)
        with login_container:
            input_user = st.text_input("Username", placeholder="Enter username")
            input_pass = st.text_input("Password", type="password", placeholder="Enter password")
            btn_login = st.button("Log In", use_container_width=True)
            
            if btn_login:
                if input_user == USERNAME and input_pass == PASSWORD:
                    st.session_state["logged_in"] = True
                    st.success("Login Successful!")
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")
    st.stop()

# Logout button in sidebar if logged in
if st.sidebar.button("🔒 Log Out"):
    st.session_state["logged_in"] = False
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.success("Logged In as Admin")

# ==================================
# MAIN DASHBOARD CONTENT
# ==================================
st.title("🦁 Distributor Dashboard")
st.caption("Inventory Control, Order Fulfillment, & Sales Intelligence System")
st.divider()

# Load Datasets
@st.cache_data(ttl=60)
def load_data():
    stock_path = "stock.csv"
    forecast_path = "products_with_stock.csv"
    orders_path = "orders.csv"
    
    # Defaults in case of empty or missing files
    s_df = pd.DataFrame(columns=['Item Details', 'Unit', 'Op. Qty.', 'Qty. In', 'Qty. Out', 'Cl. Qty.'])
    f_df = pd.DataFrame(columns=['Product', 'Current_Stock', 'Month1', 'Month2', 'Month3', 'Recommended Order', 'Status'])
    o_df = pd.DataFrame(columns=['Shop/Bakery', 'Product', 'Quantity', 'Status'])
    
    if os.path.exists(stock_path):
        s_df = pd.read_csv(stock_path, sep="\t")
    if os.path.exists(forecast_path):
        f_df = pd.read_csv(forecast_path)
    if os.path.exists(orders_path):
        o_df = pd.read_csv(orders_path)
        
    return s_df, f_df, o_df

try:
    stock_df, forecast_df, orders_df = load_data()
except Exception as e:
    st.error(f"Error loading datasets: {e}")
    st.stop()

# ==================================
# KPI CALCULATIONS
# ==================================
# 1. Total Products in Master Stock (ignoring empty rows/total footer rows)
valid_master_items = stock_df[stock_df['Item Details'].str.strip() != ""] if 'Item Details' in stock_df.columns else stock_df
total_products = len(valid_master_items)

# 2. Low Stock Alerts (Current_Stock < 50 in products_with_stock)
low_stock_count = len(forecast_df[forecast_df['Current_Stock'] < 50]) if 'Current_Stock' in forecast_df.columns else 0

# 3. Pending Orders (Status is 'Processing' or 'Shipped')
pending_orders = len(orders_df[orders_df['Status'].isin(['Processing', 'Shipped'])]) if 'Status' in orders_df.columns else 0

# 4. Total Sales Volume (Sum of Quantities in delivered orders)
total_sales_volume = 0
if 'Quantity' in orders_df.columns:
    total_sales_volume = orders_df['Quantity'].sum()

# ==================================
# KPI WIDGETS DISPLAY
# ==================================
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

with kpi_col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">📦 Total Products</div>
        <div class="metric-value">{total_products}</div>
        <div class="metric-desc">Master catalog items</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">⚠️ Low Stock Alerts</div>
        <div class="metric-value" style="color: {'#EF4444' if low_stock_count > 0 else '#10B981'};">{low_stock_count}</div>
        <div class="metric-desc">Products under 50 units</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">⏳ Pending Orders</div>
        <div class="metric-value">{pending_orders}</div>
        <div class="metric-desc">Processing or Shipped</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">📈 Total Sales Volume</div>
        <div class="metric-value">{total_sales_volume}</div>
        <div class="metric-desc">Total quantities ordered</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")
st.write("")

# ==================================
# FORECASTING DETAILS & CHARTS
# ==================================
left_col, right_col = st.columns([1.2, 0.8])

with left_col:
    st.subheader("📊 Sales Forecasting & Recommended Reorders")
    
    forecast_df_display = forecast_df.copy()
    if not forecast_df_display.empty and 'Month1' in forecast_df_display.columns:
        recommended_orders = []
        status_list = []
        for index, row in forecast_df_display.iterrows():
            try:
                inc1 = row["Month2"] - row["Month1"]
                inc2 = row["Month3"] - row["Month2"]
                avg_inc = (inc1 + inc2) / 2
                pred = row["Month3"] + avg_inc
                rec = max(0, round(pred * 1.1))
                recommended_orders.append(rec)
                
                if row["Current_Stock"] < rec:
                    status_list.append("🔴 LOW STOCK")
                else:
                    status_list.append("🟢 OK")
            except Exception:
                recommended_orders.append(0)
                status_list.append("UNKNOWN")
                
        forecast_df_display["Recommended Order"] = recommended_orders
        forecast_df_display["Status"] = status_list

    st.dataframe(
        forecast_df_display[['Product', 'Current_Stock', 'Recommended Order', 'Status']],
        use_container_width=True,
        hide_index=True
    )

with right_col:
    st.subheader("🏆 Top Selling Products")
    if not forecast_df.empty and 'Month3' in forecast_df.columns:
        top_product_row = forecast_df.loc[forecast_df["Month3"].idxmax()]
        st.success(
            f"**{top_product_row['Product']}** is the highest selling product, with **{int(top_product_row['Month3'])}** units sold in the last month."
        )
    else:
        st.info("No sales data available to calculate top selling product.")

st.divider()

# ==================================
# ANALYTICS GRAPH SECTION
# ==================================
st.subheader("📈 Business Visualizations")
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    if not forecast_df.empty and 'Month1' in forecast_df.columns:
        # Melt dataframe for multi-month bar chart
        melted_df = forecast_df.melt(
            id_vars="Product",
            value_vars=["Month1", "Month2", "Month3"],
            var_name="Month",
            value_name="Sales"
        )
        
        # Style Plotly chart with nice colors and layout
        fig = px.bar(
            melted_df,
            x="Product",
            y="Sales",
            color="Month",
            barmode="group",
            title="Monthly Product Sales Trends",
            color_discrete_sequence=["#1E3A8A", "#3B82F6", "#60A5FA"]
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend_title_text="",
            xaxis_title="",
            yaxis_title="Units Sold",
            font=dict(family="Inter, sans-serif")
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No forecasting data available for charts.")

with chart_col2:
    if not forecast_df.empty and 'Current_Stock' in forecast_df.columns:
        fig2 = px.pie(
            forecast_df,
            names="Product",
            values="Current_Stock",
            title="Current Stock Share by Product",
            color_discrete_sequence=px.colors.sequential.Blues_r
        )
        fig2.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif")
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No stock data available for charts.")
