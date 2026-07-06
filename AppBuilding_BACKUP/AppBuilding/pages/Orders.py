import streamlit as st
import pandas as pd

st.title("Orders")

orders_df = pd.read_csv("orders.csv")

st.dataframe(
    orders_df,
    use_container_width=True,
    hide_index=True
)