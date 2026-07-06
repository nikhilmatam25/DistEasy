import streamlit as st
import pandas as pd
import os



# ==================================
# LOGIN PROTECTION
# ==================================
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("⚠️ Access Denied. Please log in on the Home page first.")
    st.stop()

# ==================================
# LOAD DATA
# ==================================
def load_stock_data():
    stock_path = "stock.csv"
    if os.path.exists(stock_path):
        return pd.read_csv(stock_path, sep="\t")
    return pd.DataFrame(columns=['Item Details', 'Unit', 'Op. Qty.', 'Qty. In', 'Qty. Out', 'Cl. Qty.'])

def load_forecast_data():
    forecast_path = "products_with_stock.csv"
    if os.path.exists(forecast_path):
        return pd.read_csv(forecast_path)
    return pd.DataFrame(columns=['Product', 'Current_Stock', 'Month1', 'Month2', 'Month3', 'Recommended Order', 'Status'])

stock_df = load_stock_data()
forecast_df = load_forecast_data()

# Ensure numeric columns are floats
for col in ['Op. Qty.', 'Qty. In', 'Qty. Out', 'Cl. Qty.']:
    if col in stock_df.columns:
        stock_df[col] = pd.to_numeric(stock_df[col], errors='coerce').fillna(0.0)

# ==================================
# PAGE LAYOUT
# ==================================
st.title("📦 Inventory Management")
st.caption("Manage Master Stock Catalog and Demand Forecasting Products")
st.divider()

# Tabs for Master Inventory vs Forecasting
tab1, tab2 = st.tabs(["📋 Master Inventory (stock.csv)", "🔮 Forecasting Stock (products_with_stock.csv)"])

# ==================================
# TAB 1: MASTER INVENTORY
# ==================================
with tab1:
    st.subheader("Master Stock Directory")
    
    # Filters
    search_col, filter_col = st.columns([2, 1])
    
    with search_col:
        search_query = st.text_input("🔍 Search Products by Name", placeholder="e.g. Dates, Honey, seeds")
        
    with filter_col:
        stock_filter = st.selectbox(
            "Filter by Stock Level",
            ["All Items", "Low Stock (< 10 units)", "Out of Stock (0 units)", "Normal Stock (>= 10 units)"]
        )
    
    # Apply search and filter
    filtered_stock = stock_df.copy()
    
    # Filter out empty item rows
    filtered_stock = filtered_stock[filtered_stock['Item Details'].str.strip() != ""]
    
    if search_query:
        filtered_stock = filtered_stock[
            filtered_stock['Item Details'].str.contains(search_query, case=False, na=False)
        ]
        
    if stock_filter == "Low Stock (< 10 units)":
        filtered_stock = filtered_stock[filtered_stock['Cl. Qty.'] < 10]
    elif stock_filter == "Out of Stock (0 units)":
        filtered_stock = filtered_stock[filtered_stock['Cl. Qty.'] <= 0]
    elif stock_filter == "Normal Stock (>= 10 units)":
        filtered_stock = filtered_stock[filtered_stock['Cl. Qty.'] >= 10]
        
    # Stats summary for master stock
    st.write(f"Showing **{len(filtered_stock)}** items matching your criteria.")
    
    st.dataframe(
        filtered_stock,
        use_container_width=True,
        hide_index=True
    )
    
    # Download master stock report
    csv_master = filtered_stock.to_csv(sep="\t", index=False)
    st.download_button(
        label="📥 Download Master Stock CSV",
        data=csv_master,
        file_name="master_stock_report.csv",
        mime="text/tab-separated-values"
    )
    
    st.divider()
    
    # Update Stock Section
    st.subheader("🔄 Update Product Stock Level")
    
    # Select product to update
    valid_products_list = stock_df[stock_df['Item Details'].str.strip() != ""]['Item Details'].tolist()
    
    selected_prod = st.selectbox(
        "Select Product to Adjust",
        options=["-- Choose Product --"] + valid_products_list
    )
    
    if selected_prod != "-- Choose Product --":
        # Get product row
        idx = stock_df[stock_df['Item Details'] == selected_prod].index[0]
        row = stock_df.loc[idx]
        
        st.info(f"**Current Closing Stock**: {row['Cl. Qty.']} {row['Unit']}")
        
        col_in, col_out, col_op = st.columns(3)
        
        with col_op:
            new_op = st.number_input(
                "Opening Quantity", 
                min_value=0.0, 
                value=float(row['Op. Qty.']), 
                step=1.0,
                help="Stock at the start of period"
            )
            
        with col_in:
            new_in = st.number_input(
                "Quantity Received (Qty. In)", 
                min_value=0.0, 
                value=float(row['Qty. In']), 
                step=1.0,
                help="Add to stock"
            )
            
        with col_out:
            new_out = st.number_input(
                "Quantity Dispatched (Qty. Out)", 
                min_value=0.0, 
                value=float(row['Qty. Out']), 
                step=1.0,
                help="Remove from stock"
            )
            
        # Recalculate closing quantity automatically
        recalc_cl = new_op + new_in - new_out
        st.markdown(f"**New Calculated Closing Quantity**: `{recalc_cl:.2f}` {row['Unit']}")
        
        if st.button("💾 Save Stock Changes"):
            # Apply changes
            stock_df.loc[idx, 'Op. Qty.'] = new_op
            stock_df.loc[idx, 'Qty. In'] = new_in
            stock_df.loc[idx, 'Qty. Out'] = new_out
            stock_df.loc[idx, 'Cl. Qty.'] = recalc_cl
            
            # Save back to csv (with tab separator)
            stock_df.to_csv("stock.csv", sep="\t", index=False)
            st.success(f"Successfully updated '{selected_prod}' stock levels!")
            st.rerun()

# ==================================
# TAB 2: FORECASTING INVENTORY
# ==================================
with tab2:
    st.subheader("Demand Forecasting Products")
    
    search_f = st.text_input("🔍 Search Forecasting Products", placeholder="e.g. Dates, Honey")
    status_f = st.selectbox("Filter by Status", ["All Statuses", "LOW STOCK", "OK"])
    
    filtered_f = forecast_df.copy()
    if search_f:
        filtered_f = filtered_f[filtered_f['Product'].str.contains(search_f, case=False, na=False)]
    if status_f == "LOW STOCK":
        filtered_f = filtered_f[filtered_f['Status'] == 'LOW STOCK']
    elif status_f == "OK":
        filtered_f = filtered_f[filtered_f['Status'] == 'OK']
        
    st.dataframe(filtered_f, use_container_width=True, hide_index=True)
    
    st.divider()
    
    col_act1, col_act2 = st.columns(2)
    
    with col_act1:
        st.subheader("➕ Add New Forecasting Product")
        with st.form("add_forecast_form", clear_on_submit=True):
            new_f_name = st.text_input("Product Name")
            new_f_stock = st.number_input("Current Stock", min_value=0, value=0)
            new_f_m1 = st.number_input("Month 1 Sales", min_value=0, value=0)
            new_f_m2 = st.number_input("Month 2 Sales", min_value=0, value=0)
            new_f_m3 = st.number_input("Month 3 Sales", min_value=0, value=0)
            
            btn_add_f = st.form_submit_button("Add Forecasting Product")
            
            if btn_add_f:
                if not new_f_name.strip():
                    st.error("Please enter a valid product name")
                elif new_f_name in forecast_df['Product'].values:
                    st.error("Product already exists in forecasting database")
                else:
                    inc1 = new_f_m2 - new_f_m1
                    inc2 = new_f_m3 - new_f_m2
                    avg_inc = (inc1 + inc2) / 2
                    pred = new_f_m3 + avg_inc
                    rec = max(0, round(pred * 1.1))
                    status = "LOW STOCK" if new_f_stock < rec else "OK"
                    
                    new_row = pd.DataFrame({
                        "Product": [new_f_name],
                        "Current_Stock": [new_f_stock],
                        "Month1": [new_f_m1],
                        "Month2": [new_f_m2],
                        "Month3": [new_f_m3],
                        "Recommended Order": [rec],
                        "Status": [status]
                    })
                    
                    forecast_df = pd.concat([forecast_df, new_row], ignore_index=True)
                    forecast_df.to_csv("products_with_stock.csv", index=False)
                    st.success(f"Added forecasting product '{new_f_name}'!")
                    st.rerun()

    with col_act2:
        st.subheader("🔄 Update Stock or Delete Product")
        
        selected_f_prod = st.selectbox(
            "Select Forecasting Product to Manage",
            options=["-- Choose Product --"] + forecast_df['Product'].tolist()
        )
        
        if selected_f_prod != "-- Choose Product --":
            f_row = forecast_df[forecast_df['Product'] == selected_f_prod].iloc[0]
            
            st.markdown(f"**Current Stock**: `{f_row['Current_Stock']}` | **Status**: `{f_row['Status']}`")
            
            new_f_stock_val = st.number_input("New Current Stock Value", min_value=0, value=int(f_row['Current_Stock']))
            
            sub_col1, sub_col2 = st.columns(2)
            with sub_col1:
                if st.button("Update Stock Level"):
                    rec = f_row['Recommended Order']
                    status = "LOW STOCK" if new_f_stock_val < rec else "OK"
                    
                    forecast_df.loc[forecast_df['Product'] == selected_f_prod, 'Current_Stock'] = new_f_stock_val
                    forecast_df.loc[forecast_df['Product'] == selected_f_prod, 'Status'] = status
                    
                    forecast_df.to_csv("products_with_stock.csv", index=False)
                    st.success("Stock level updated successfully!")
                    st.rerun()
                    
            with sub_col2:
                if st.button("🗑️ Delete Product from Forecast", type="primary"):
                    forecast_df = forecast_df[forecast_df['Product'] != selected_f_prod]
                    forecast_df.to_csv("products_with_stock.csv", index=False)
                    st.success("Product deleted successfully!")
                    st.rerun()
