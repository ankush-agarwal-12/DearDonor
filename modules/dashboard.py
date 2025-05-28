print("🔄 LOADING dashboard.py")
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from modules.airtable_utils import fetch_all_donations
from datetime import datetime

def show_dashboard():
    st.title("🔖 Donation Dashboard")

    donations = fetch_all_donations()

    if not donations:
        st.warning("No donation data found.")
        st.stop()

    # Convert to DataFrame
    df = pd.DataFrame(donations)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Month'] = df['Date'].dt.to_period('M')

    # Top Summary
    st.metric("Total Donations", f"₹{df['Amount'].sum():,.0f}")
    st.metric("Total Entries", len(df))

    # Charts
    st.subheader("📈 Donations Over Time")
    monthly_total = df.groupby('Month')['Amount'].sum()
    st.line_chart(monthly_total)

    st.subheader("🏆 Top Donors")
    top_donors = df.groupby('Donor')['Amount'].sum().sort_values(ascending=False).head(5)
    st.bar_chart(top_donors)

    st.subheader("💳 Mode of Payment Breakdown")
    mode_counts = df['Mode'].value_counts()
    st.bar_chart(mode_counts)
