import streamlit as st
import pandas as pd
import os

# ==================================
# PAGE CONFIGURATION
# ==================================
st.set_page_config(
    page_title="LION Customers Database",
    page_icon="👥",
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
def load_customers_data():
    customers_path = "customers.csv"
    if os.path.exists(customers_path):
        return pd.read_csv(customers_path)
    # Return empty template if not exists
    return pd.DataFrame(columns=['Customer Name', 'Contact Person', 'Phone', 'Address', 'Outstanding Balance'])

customers_df = load_customers_data()

# Ensure Outstanding Balance is numeric
if 'Outstanding Balance' in customers_df.columns:
    customers_df['Outstanding Balance'] = pd.to_numeric(customers_df['Outstanding Balance'], errors='coerce').fillna(0.0)

# ==================================
# PAGE CONTENT & LAYOUT
# ==================================
st.title("👥 Retailers / Customers Directory")
st.caption("Manage business client records, contact details, and outstanding balances")
st.divider()

# Search Bar for Customers
search_query = st.text_input("🔍 Search Customer Records", placeholder="Search by name, contact, phone, or address...")

filtered_df = customers_df.copy()

if search_query:
    filtered_df = filtered_df[
        filtered_df['Customer Name'].str.contains(search_query, case=False, na=False) |
        filtered_df['Contact Person'].str.contains(search_query, case=False, na=False) |
        filtered_df['Phone'].astype(str).str.contains(search_query, case=False, na=False) |
        filtered_df['Address'].str.contains(search_query, case=False, na=False)
    ]

# Display stats
total_clients = len(customers_df)
total_outstanding = customers_df['Outstanding Balance'].sum() if 'Outstanding Balance' in customers_df.columns else 0.0

col_c1, col_c2 = st.columns(2)
with col_c1:
    st.metric("Total Registered Retailers", total_clients)
with col_c2:
    st.metric("Total Outstanding Balance (Receivables) 💳", f"₹{total_outstanding:,.2f}")

st.write("")

# Display Customer Directory Table
st.dataframe(
    filtered_df,
    use_container_width=True,
    hide_index=True
)

st.divider()

# Side-by-side operations: Record Payment vs Add/Edit Client
col_left, col_right = st.columns(2)

# ==================================
# LEFT COLUMN: RECORD CLIENT PAYMENTS
# ==================================
with col_left:
    st.subheader("💳 Record Payment Received")
    
    if customers_df.empty:
        st.info("No registered customers found. Please add a customer first.")
    else:
        # Select customer
        client_options = customers_df['Customer Name'].dropna().unique().tolist()
        pay_client = st.selectbox(
            "Select Customer Making Payment",
            options=["-- Choose Customer --"] + client_options,
            key="pay_select"
        )
        
        if pay_client != "-- Choose Customer --":
            # Get outstanding balance
            idx = customers_df[customers_df['Customer Name'] == pay_client].index[0]
            current_balance = float(customers_df.loc[idx, 'Outstanding Balance'])
            
            st.info(f"**Current Outstanding Balance**: ₹{current_balance:,.2f}")
            
            pay_amt = st.number_input(
                "Payment Amount Received (₹)", 
                min_value=0.0, 
                max_value=max(0.0, current_balance), 
                value=0.0, 
                step=100.0,
                help="Amount will be deducted from outstanding balance"
            )
            
            new_balance = current_balance - pay_amt
            st.markdown(f"**New Calculated Balance**: `₹{new_balance:,.2f}`")
            
            if st.button("Save Payment Record", use_container_width=True):
                # Update balance
                customers_df.loc[idx, 'Outstanding Balance'] = new_balance
                customers_df.to_csv("customers.csv", index=False)
                st.success(f"Recorded payment of ₹{pay_amt:,.2f} for **{pay_client}**!")
                st.rerun()

# ==================================
# RIGHT COLUMN: ADD / EDIT CUSTOMERS
# ==================================
with col_right:
    # Sub tabs for Add vs Edit
    tab_add, tab_edit = st.tabs(["➕ Add New Customer", "✏️ Edit Customer Details"])
    
    with tab_add:
        with st.form("add_customer_form", clear_on_submit=True):
            new_name = st.text_input("Customer/Shop Name")
            new_contact = st.text_input("Contact Person Name")
            new_phone = st.text_input("Phone Number")
            new_address = st.text_input("Address")
            new_balance = st.number_input("Initial Outstanding Balance (₹)", min_value=0.0, value=0.0, step=100.0)
            
            btn_add_customer = st.form_submit_button("Register Customer", use_container_width=True)
            
            if btn_add_customer:
                if not new_name.strip():
                    st.error("Please enter a valid Customer Name")
                elif new_name in customers_df['Customer Name'].values:
                    st.error("A customer with this name already exists")
                else:
                    new_cust_row = pd.DataFrame({
                        "Customer Name": [new_name],
                        "Contact Person": [new_contact],
                        "Phone": [new_phone],
                        "Address": [new_address],
                        "Outstanding Balance": [new_balance]
                    })
                    
                    customers_df = pd.concat([customers_df, new_cust_row], ignore_index=True)
                    customers_df.to_csv("customers.csv", index=False)
                    st.success(f"Customer **{new_name}** successfully registered!")
                    st.rerun()
                    
    with tab_edit:
        if customers_df.empty:
            st.info("No customers available to edit.")
        else:
            edit_client = st.selectbox(
                "Select Customer to Edit",
                options=["-- Choose Customer --"] + customers_df['Customer Name'].dropna().unique().tolist(),
                key="edit_select"
            )
            
            if edit_client != "-- Choose Customer --":
                edit_idx = customers_df[customers_df['Customer Name'] == edit_client].index[0]
                edit_row = customers_df.loc[edit_idx]
                
                with st.form("edit_customer_form"):
                    updated_contact = st.text_input("Contact Person Name", value=str(edit_row['Contact Person']))
                    updated_phone = st.text_input("Phone Number", value=str(edit_row['Phone']))
                    updated_address = st.text_input("Address", value=str(edit_row['Address']))
                    updated_balance = st.number_input("Outstanding Balance (₹)", min_value=0.0, value=float(edit_row['Outstanding Balance']), step=100.0)
                    
                    btn_save_changes = st.form_submit_button("Save Changes", use_container_width=True)
                    
                    if btn_save_changes:
                        customers_df.loc[edit_idx, 'Contact Person'] = updated_contact
                        customers_df.loc[edit_idx, 'Phone'] = updated_phone
                        customers_df.loc[edit_idx, 'Address'] = updated_address
                        customers_df.loc[edit_idx, 'Outstanding Balance'] = updated_balance
                        
                        customers_df.to_csv("customers.csv", index=False)
                        st.success(f"Saved changes for **{edit_client}**!")
                        st.rerun()
