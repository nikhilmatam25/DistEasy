import streamlit as st
import pandas as pd
import plotly.express as px

# ==================================
# PAGE SETTINGS
# ==================================

st.set_page_config(
    page_title="LION Stock Predictor",
    layout="wide"
)


# ==================================
# LOGIN SYSTEM
# ==================================

USERNAME = "admin"
PASSWORD = "lion123"

st.sidebar.header("Login")

username = st.sidebar.text_input("Username")
password = st.sidebar.text_input(
    "Password",
    type="password"
)

if username != USERNAME or password != PASSWORD:
    st.warning("Please login to continue")
    st.stop()
st.session_state["logged_in"] = True 
st.caption(
    "Inventory Management and Demand Forecasting System"
)
st.divider()

st.header("Current Stock Report")

stock_df = pd.read_csv("stock.csv")

st.dataframe(
    stock_df,
    use_container_width=True,
    hide_index=True
)
# ==================================
# LOAD DATA
# ==================================

df = pd.read_csv("products_with_stock.csv")

# ==================================
# ADD PRODUCT
# ==================================

st.sidebar.header("Add New Product")

new_product = st.sidebar.text_input("Product Name")

new_stock = st.sidebar.number_input(
    "Current Stock",
    min_value=0,
    value=0
)

new_month1 = st.sidebar.number_input(
    "Month1 Sales",
    min_value=0,
    value=0,
    key="month1"
)

new_month2 = st.sidebar.number_input(
    "Month2 Sales",
    min_value=0,
    value=0,
    key="month2"
)

new_month3 = st.sidebar.number_input(
    "Month3 Sales",
    min_value=0,
    value=0,
    key="month3"
)

if st.sidebar.button("Add Product"):

    new_row = pd.DataFrame({
        "Product": [new_product],
        "Current_Stock": [new_stock],
        "Month1": [new_month1],
        "Month2": [new_month2],
        "Month3": [new_month3]
    })

    df = pd.concat(
        [df, new_row],
        ignore_index=True
    )

    df.to_csv(
        "products_with_stock.csv",
        index=False
    )

    st.sidebar.success("Product Added")

# ==================================
# DELETE PRODUCT
# ==================================

st.sidebar.header("Delete Product")

product_to_delete = st.sidebar.selectbox(
    "Select Product",
    df["Product"],
    key="delete_product"
)

if st.sidebar.button("Delete Product"):

    df = df[
        df["Product"] != product_to_delete
    ]

    df.to_csv(
        "products_with_stock.csv",
        index=False
    )

    st.sidebar.success("Product Deleted")

# ==================================
# UPDATE STOCK
# ==================================

st.sidebar.header("Update Stock")

product_to_update = st.sidebar.selectbox(
    "Choose Product",
    df["Product"],
    key="update_product"
)

new_stock_value = st.sidebar.number_input(
    "New Stock Value",
    min_value=0,
    value=0,
    key="stock_update"
)

if st.sidebar.button("Update Stock"):

    df.loc[
        df["Product"] == product_to_update,
        "Current_Stock"
    ] = new_stock_value

    df.to_csv(
        "products_with_stock.csv",
        index=False
    )

    st.sidebar.success("Stock Updated")

# ==================================
# PREDICTION LOGIC
# ==================================

recommended_orders = []
status_list = []

for index, row in df.iterrows():

    increase1 = row["Month2"] - row["Month1"]
    increase2 = row["Month3"] - row["Month2"]

    average_increase = (
        increase1 + increase2
    ) / 2

    next_month_prediction = (
        row["Month3"] + average_increase
    )

    recommended_order = round(
        next_month_prediction * 1.1
    )

    recommended_orders.append(
        recommended_order
    )

    if row["Current_Stock"] < recommended_order:
        status_list.append(
            "LOW STOCK"
        )
    else:
        status_list.append(
            "OK"
        )

df["Recommended Order"] = recommended_orders
df["Status"] = status_list

# ==================================
# SUMMARY
# ==================================

st.subheader("Summary")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Total Products",
        len(df)
    )

with col2:
    st.metric(
        "Low Stock Products",
        len(
            df[
                df["Current_Stock"] < 50
            ]
        )
    )
with col3:

    highest_product = df.loc[
        df["Month3"].idxmax(),
        "Product"
    ]

    st.metric(
        "Highest Selling Product",
        highest_product
    )
st.divider()
# ==================================
# TOP PRODUCT
# ==================================

st.subheader("🏆 Top Selling Product")

highest_product = df.loc[
    df["Month3"].idxmax()
]

st.success(
    f"{highest_product['Product']} sold {highest_product['Month3']} units in Month3"
)

# ==================================
# SEARCH
# ==================================

st.subheader("Search Product")

search = st.text_input(
    "Enter Product Name"
)

# ==================================
# FILTER
# ==================================

status_filter = st.selectbox(
    "Filter Products",
    [
        "All",
        "Low Stock",
        "Normal Stock"
    ]
)

result_df = df.copy()

if search:

    result_df = result_df[
        result_df["Product"].str.contains(
            search,
            case=False,
            na=False
        )
    ]

if status_filter == "Low Stock":

    result_df = result_df[
        result_df["Current_Stock"] < 50
    ]

elif status_filter == "Normal Stock":

    result_df = result_df[
        result_df["Current_Stock"] >= 50
    ]

# ==================================
# PRODUCTS TABLE
# ==================================

st.subheader("Products")

display_df = result_df[
    [
        "Product",
        "Current_Stock",
        "Recommended Order",
        "Status"
    ]
].copy()

display_df.insert(
    0,
    "S.No",
    range(
        1,
        len(display_df) + 1
    )
)

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)

# ==================================
# LOW STOCK TABLE
# ==================================

st.subheader(
    "Low Stock Products"
)

low_stock = df[
    df["Current_Stock"] < 50
].copy()

low_stock.insert(
    0,
    "S.No",
    range(
        1,
        len(low_stock) + 1
    )
)

st.dataframe(
    low_stock,
    use_container_width=True,
    hide_index=True
)

# ==================================
# SALES CHART
# ==================================

st.subheader(
    "Sales Comparison Chart"
)

chart_df = df.melt(
    id_vars="Product",
    value_vars=[
        "Month1",
        "Month2",
        "Month3"
    ],
    var_name="Month",
    value_name="Sales"
)

fig = px.bar(
    chart_df,
    x="Product",
    y="Sales",
    color="Month",
    barmode="group",
    title="Monthly Sales Comparison"
)

st.plotly_chart(
    fig,
    use_container_width=True
)
st.subheader("Stock Distribution")

fig2 = px.pie(
    df,
    names="Product",
    values="Current_Stock",
    title="Current Stock Distribution"
)

st.plotly_chart(
    fig2,
    use_container_width=True
)
# ==================================
# DOWNLOAD REPORT
# ==================================

st.subheader("Download Report")

csv = df.to_csv(index=False)

st.download_button(
    label="Download Stock Report",
    data=csv,
    file_name="stock_report.csv",
    mime="text/csv"
)

