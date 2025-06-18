import streamlit as st
import pandas as pd
import plotly.express as px

# ✅ Set page config
st.set_page_config(layout="wide", page_title="Telecom BI Dashboard")

# ✅ Load data
@st.cache_data
def load_data():
    customer = pd.read_csv("customer_master_data.csv", parse_dates=["JoinDate", "TerminationDate"])
    billing = pd.read_csv("billing_data.csv")
    offers = pd.read_csv("offer_campaign_data.csv")
    support = pd.read_csv("customer_support_data.csv", parse_dates=["ContactDate"])
    return customer, billing, offers, support

customer, billing, offers, support = load_data()

# ✅ Add churn flag
customer["Churn"] = customer["TerminationDate"].notna().astype(int)

# ✅ Fix billing date
billing["Month"] = pd.to_datetime(billing["Month"], format="%Y-%m")

# ✅ Merge customer with billing
billing_merged = pd.merge(billing, customer, on="CustomerID", how="left")

# ✅ Churn Trend by Segment
churn_trend = (
    customer[customer["Churn"] == 1]
    .dropna(subset=["TerminationDate"])
    .groupby([customer["TerminationDate"].dt.to_period("M").dt.to_timestamp(), "Segment"])
    .size()
    .reset_index(name="ChurnCount")
)

# ✅ Revenue at Risk: last billing amounts of churned customers
last_bills = (
    billing_merged[billing_merged["Churn"] == 1]
    .sort_values("Month")
    .groupby("CustomerID")
    .tail(1)
)

# ✅ Support metrics
support_agg = support.groupby("CustomerID").agg(
    NumComplaints=("IssueCategory", "count"),
    AvgResolutionTime=("ResolutionTime", "mean")
).reset_index()

merged_support = pd.merge(customer, support_agg, on="CustomerID", how="left")
merged_support["AvgResolutionTime"] = merged_support["AvgResolutionTime"].fillna(0)
merged_support["NumComplaints"] = merged_support["NumComplaints"].fillna(0)

# ---------- Streamlit UI ---------- #

st.title("📊 Telecom Churn & Revenue Retention Dashboard")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Churn Trend",
    "Revenue at Risk",
    "Offer Impact",
    "Regional Heatmap",
    "Support vs Churn"
])

# ✅ TAB 1: Churn Trend
with tab1:
    st.subheader("📉 Monthly Churn Trend by Segment")
    st.markdown("""
        This chart shows the number of customers who terminated their services over time.
        It is grouped by segment to help identify which customer types (e.g., Premium, Mass, Youth)
        are churning the most in each month. This is useful for trend analysis and identifying peak churn periods.
    """)
    fig = px.line(
        churn_trend,
        x="TerminationDate",
        y="ChurnCount",
        color="Segment",
        markers=True,
        title="Churned Customers Over Time"
    )
    st.plotly_chart(fig, use_container_width=True)

# ✅ TAB 2: Revenue at Risk
with tab2:
    st.subheader("💸 Revenue at Risk Due to Churn")
    st.markdown("""
        This section estimates the potential revenue loss from customers who have churned,
        based on their most recent bill amount before termination. Understanding the distribution
        of last bills helps quantify revenue at risk and prioritize retention strategies for high-value customers.
    """)
    fig2 = px.histogram(
        last_bills,
        x="Amount",
        nbins=40,
        title="Last Bill Amounts of Churned Customers"
    )
    st.plotly_chart(fig2, use_container_width=True)
    st.metric("Total Revenue at Risk", f"${last_bills['Amount'].sum():,.2f}")

# ✅ TAB 3: Offer Redemption Rates
with tab3:
    st.subheader("🎁 Offer Redemption Rate by Segment and Type")
    st.markdown("""
        This bar chart compares how different segments responded to various marketing offers.
        A higher redemption rate indicates better campaign effectiveness. You can use this insight
        to target future offers more effectively and reduce churn by segment.
    """)
    fig3 = px.bar(
        offers,
        x="TargetSegment",
        y="RedemptionRate",
        color="OfferType",
        barmode="group",
        title="Offer Effectiveness"
    )
    st.plotly_chart(fig3, use_container_width=True)

# ✅ TAB 4: Region-wise Churn Rate
with tab4:
    st.subheader("🌍 Churn Rate by Region")
    st.markdown("""
        This visualization highlights the average churn rate across different regions.
        Identifying high-churn regions helps in localizing customer retention strategies,
        optimizing service quality, or addressing regional-specific concerns.
    """)
    region_churn = customer.groupby("Region")["Churn"].mean().reset_index()
    fig4 = px.bar(
        region_churn,
        x="Region",
        y="Churn",
        color="Churn",
        color_continuous_scale="reds",
        title="Average Churn Rate by Region"
    )
    st.plotly_chart(fig4, use_container_width=True)

# ✅ TAB 5: Support vs Churn
with tab5:
    st.subheader("📞 Customer Support Impact on Churn")
    st.markdown("""
        This scatter plot shows the relationship between customer complaints and churn.
        Each point represents a customer. More complaints and longer resolution times may
        correlate with higher churn, suggesting a need to improve support services for better retention.
    """)
    fig5 = px.scatter(
        merged_support,
        x="NumComplaints",
        y="AvgResolutionTime",
        color=merged_support["Churn"].map({1: "Churned", 0: "Active"}),
        size="AvgResolutionTime",
        hover_data=["CustomerID"],
        title="Complaints vs Resolution Time"
    )
    st.plotly_chart(fig5, use_container_width=True)
