# streamlit_app.py

"""Streamlit dashboard for Bluestocks Mutual Funds.

This app loads the generated `dashboard/dashboard_data.json` and presents
interactive visualisations using Plotly. It is a minimal placeholder that can
be expanded with more sophisticated UI components later.
"""

import json
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Bluestocks Dashboard", layout="wide")

st.title("Bluestocks Mutual Funds Dashboard")

# Load the dashboard JSON data
@st.cache_data
def load_dashboard_data():
    with open("dashboard/dashboard_data.json", "r", encoding="utf-8") as f:
        return json.load(f)

data = load_dashboard_data()

# Example: show total NAV per fund as a bar chart
if "funds" in data:
    funds = data["funds"]
    navs = [f.get("total_nav", 0) for f in funds]
    names = [f.get("name", "Unnamed") for f in funds]
    df = {"Fund": names, "Total NAV": navs}
    fig = px.bar(df, x="Fund", y="Total NAV", title="Total NAV by Fund")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No fund data found in dashboard JSON.")

st.info("This is a basic placeholder. Extend with more charts, filters, and navigation as needed.")
