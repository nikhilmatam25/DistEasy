import streamlit as st
import pandas as pd
import os

# ==================================
# PAGE CONFIGURATION
# ==================================
st.set_page_config(
    page_title="LION Order Management",
    page_icon="🛒",
    layout="wide"
)

# ==================================
# LOGIN PROTECTION
# ==================================
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("⚠️ Access Denied. Please log in on the Home page first.")
    st.stop()

# ==================================
# LOAD DATA
# ==================================
def load_data():
    orders_path = "orders.csv"
    stock_path = "stock.csv"
    forecast_path = "products_with_stock.csv"
    customers_path = "customers.csv"
    
    o_df = pd.read_csv(orders_path) if os.path.exists(orders_path) else pd.DataFrame(columns=['Shop/Bakery', 'Product', 'Quantity', 'Status'])
    s_df = pd.read_csv(stock_path, sep="\t") if os.path.exists(stock_path) else pd.DataFrame(columns=['Item Details', 'Unit', 'Op. Qty.', 'Qty. In', 'Qty. Out', 'Cl. Qty.'])
    f_df = pd.read_csv(forecast_path) if os.path.exists(forecast_path) else pd.DataFrame(columns=['Product', 'Current_Stock', 'Month1', 'Month2', 'Month3', 'Recommended Order', 'Status'])
    c_df = pd.read_csv(customers_path) if os.path.exists(customers_path) else pd.DataFrame(columns=['Customer Name', 'Contact Person', 'Phone', 'Address', 'Outstanding Balance'])
    
    return o_df, s_df, f_df, c_df

orders_df, stock_df, forecast_df, customers_df = load_data()

# Ensure stock numeric values are valid
for col in ['Op. Qty.', 'Qty. In', 'Qty. Out', 'Cl. Qty.']:
    if col in stock_df.columns:
        stock_df[col] = pd.to_numeric(stock_df[col], errors='coerce').fillna(0.0)

# ==================================
# ORDER STOCK INTEGRATION LOGIC
# ==================================
def process_stock_deduction(product_name, quantity):
    deducted_stock = False
    deducted_forecast = False
    
    stock_file_msg = ""
    forecast_file_msg = ""
    
    # 1. Update stock.csv (Master Inventory)
    # Search for an exact match first, then a substring match
    matched_idx = None
    exact_matches = stock_df[stock_df['Item Details'] == product_name]
    if not exact_matches.empty:
        matched_idx = exact_matches.index[0]
    else:
        substring_matches = stock_df[stock_df['Item Details'].str.contains(product_name, case=False, na=False)]
        if not substring_matches.empty:
            matched_idx = substring_matches.index[0]
            
    if matched_idx is not None:
        p_name = stock_df.loc[matched_idx, 'Item Details']
        # Increase Qty Out
        stock_df.loc[matched_idx, 'Qty. Out'] += float(quantity)
        # Recalculate Cl. Qty
        stock_df.loc[matched_idx, 'Cl. Qty.'] = (
            stock_df.loc[matched_idx, 'Op. Qty.'] + 
            stock_df.loc[matched_idx, 'Qty. In'] - 
            stock_df.loc[matched_idx, 'Qty. Out']
        )
        # Save stock.csv
        stock_df.to_csv("stock.csv", sep="\t", index=False)
        deducted_stock = True
        stock_file_msg = f"Deducted from Master Inventory: **{p_name}**"
        
    # 2. Update products_with_stock.csv (Forecasting)
    matched_f_idx = None
    exact_f_matches = forecast_df[forecast_df['Product'] == product_name]
    if not exact_f_matches.empty:
        matched_f_idx = exact_f_matches.index[0]
    else:
        substring_f_matches = forecast_df[forecast_df['Product'].str.contains(product_name, case=False, na=False)]
        if not substring_f_matches.empty:
            matched_f_idx = substring_f_matches.index[0]
            
    if matched_f_idx is not None:
        pf_name = forecast_df.loc[matched_f_idx, 'Product']
        # Reduce Current Stock
        forecast_df.loc[matched_f_idx, 'Current_Stock'] = max(
            0, 
            int(forecast_df.loc[matched_f_idx, 'Current_Stock'] - quantity)
        )
        # Recalculate status
        rec_ord = forecast_df.loc[matched_f_idx, 'Recommended Order']
        if pd.isna(rec_ord):
            rec_ord = 0
        forecast_df.loc[matched_f_idx, 'Status'] = "LOW STOCK" if forecast_df.loc[matched_f_idx, 'Current_Stock'] < rec_ord else "OK"
        
        # Save products_with_stock.csv
        forecast_df.to_csv("products_with_stock.csv", index=False)
        deducted_forecast = True
        forecast_file_msg = f"Deducted from Forecasting: **{pf_name}**"
        
    return deducted_stock, deducted_forecast, stock_file_msg, forecast_file_msg

# ==================================
# PAGE CONTENT & LAYOUT
# ==================================
st.title("🛒 Order Management")
st.caption("Track, fulfill, and record retail store customer orders")
st.divider()

# KPI Metrics for Orders
total_o = len(orders_df)
processing_o = len(orders_df[orders_df['Status'] == 'Processing'])
shipped_o = len(orders_df[orders_df['Status'] == 'Shipped'])
delivered_o = len(orders_df[orders_df['Status'] == 'Delivered'])

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.metric("Total Orders", total_o)
with col_m2:
    st.metric("Pending (Processing) 🟠", processing_o)
with col_m3:
    st.metric("In Transit (Shipped) 🔵", shipped_o)
with col_m4:
    st.metric("Delivered 🟢", delivered_o)

st.write("")

# Layout: Left side shows Order Table & Fulfillments, Right side shows Create New Order
left_col, right_col = st.columns([1.2, 0.8])

# ==================================
# LEFT COLUMN: ORDER DASHBOARD & ACTIONS
# ==================================
with left_col:
    st.subheader("📋 Orders Directory")
    
    # Filters
    f_status = st.selectbox("Filter Orders by Status", ["All Statuses", "Processing", "Shipped", "Delivered"])
    
    filtered_orders = orders_df.copy()
    if f_status != "All Statuses":
        filtered_orders = filtered_orders[filtered_orders['Status'] == f_status]
        
    # Append index/S.No column for display
    display_df = filtered_orders.copy()
    display_df.insert(0, "Order ID", display_df.index + 1)
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    st.divider()
    
    # Update Order Status Action
    st.subheader("🔄 Update Order Status")
    
    # Select from pending/shipped orders
    active_orders = orders_df[orders_df['Status'].isin(['Processing', 'Shipped'])]
    
    if active_orders.empty:
        st.info("No active pending or shipped orders found to fulfill.")
    else:
        active_options = {}
        for idx, r in active_orders.iterrows():
            active_options[idx] = f"ID {idx + 1} | {r['Shop/Bakery']} - {r['Product']} ({r['Quantity']} units) [{r['Status']}]"
            
        selected_order_idx = st.selectbox(
            "Select Order to Update",
            options=list(active_options.keys()),
            format_func=lambda x: active_options[x]
        )
        
        col_st, col_btn = st.columns([1.5, 1])
        with col_st:
            new_status = st.selectbox("New Status", ["Processing", "Shipped", "Delivered"])
            
        with col_btn:
            st.write("")
            st.write("")
            btn_update = st.button("Apply Status Change", use_container_width=True)
            
        if btn_update:
            old_status = orders_df.loc[selected_order_idx, 'Status']
            prod_name = orders_df.loc[selected_order_idx, 'Product']
            qty = orders_df.loc[selected_order_idx, 'Quantity']
            
            # Apply update
            orders_df.loc[selected_order_idx, 'Status'] = new_status
            orders_df.to_csv("orders.csv", index=False)
            
            # If changing to Delivered (and it wasn't already delivered)
            if old_status != "Delivered" and new_status == "Delivered":
                # Deduct stock
                d_stock, d_fore, msg_s, msg_f = process_stock_deduction(prod_name, qty)
                
                # Show integration updates
                st.success(f"Order status updated to **Delivered**!")
                if d_stock:
                    st.info(msg_s)
                if d_fore:
                    st.info(msg_f)
                if not d_stock and not d_fore:
                    st.warning("⚠️ Could not locate matching product in either inventory to deduct stock.")
            else:
                st.success(f"Order status updated from **{old_status}** to **{new_status}**.")
            st.rerun()

# ==================================
# RIGHT COLUMN: CREATE NEW ORDER
# ==================================
with right_col:
    st.subheader("➕ Create New Retailer Order")
    
    with st.form("new_order_form", clear_on_submit=True):
        # 1. Retailer selection (from customers.csv or type in)
        customer_names = []
        if not customers_df.empty and 'Customer Name' in customers_df.columns:
            customer_names = customers_df['Customer Name'].dropna().unique().tolist()
            
        shop_select = st.selectbox("Retailer / Customer", options=["-- Select Customer --", "New Customer..."] + customer_names)
        
        # If "New Customer" selected, show text input
        shop_text = ""
        if shop_select == "New Customer...":
            shop_text = st.text_input("Enter New Customer Name")
            
        # 2. Product selection (list from stock.csv and products_with_stock.csv)
        stock_prod_names = []
        if not stock_df.empty and 'Item Details' in stock_df.columns:
            stock_prod_names = stock_df[stock_df['Item Details'].str.strip() != ""]['Item Details'].tolist()
            
        fore_prod_names = []
        if not forecast_df.empty and 'Product' in forecast_df.columns:
            fore_prod_names = forecast_df['Product'].tolist()
            
        all_unique_prods = sorted(list(set(stock_prod_names + fore_prod_names)))
        
        prod_select = st.selectbox("Product Ordered", options=["-- Select Product --"] + all_unique_prods)
        
        # 3. Order Quantity
        order_qty = st.number_input("Quantity Ordered", min_value=1, value=10, step=1)
        
        btn_submit_order = st.form_submit_button("Submit Purchase Order", use_container_width=True)
        
        if btn_submit_order:
            # Resolve customer name
            resolved_customer = ""
            if shop_select == "New Customer...":
                resolved_customer = shop_text.strip()
            elif shop_select != "-- Select Customer --":
                resolved_customer = shop_select
                
            if not resolved_customer:
                st.error("Please specify a customer name.")
            elif prod_select == "-- Select Product --":
                st.error("Please choose a product.")
            else:
                # Add order as Processing
                new_order_row = pd.DataFrame({
                    "Shop/Bakery": [resolved_customer],
                    "Product": [prod_select],
                    "Quantity": [order_qty],
                    "Status": ["Processing"]
                })
                
                orders_df = pd.concat([orders_df, new_order_row], ignore_index=True)
                orders_df.to_csv("orders.csv", index=False)
                
                st.success(f"Order created successfully for **{resolved_customer}**!")
                st.rerun()
