# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from db import get_connection

# ---------------- STREAMLIT CONFIGURATION ----------------
st.set_page_config(
    page_title="Contose Sales Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- HELPER FUNCTION ----------------
def load_data(query):
    conn = get_connection()
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# ---------------- SIDEBAR ----------------
st.sidebar.title("📌 Navigation")

page = st.sidebar.radio(
    "Go to",
    [
        "🏠 Project Overview",
        "📊 Main Dashboard",
        "--- TABLES ---",
        "📄 Customers",
        "🏪 Stores",
        "📦 Products",
        "📂 Categories",
        "🗂 Subcategories",
        "📝 Orders",
        "📑 Order Line Items"
    ]
)

# ---------------- PROJECT OVERVIEW ----------------
if page == "🏠 Project Overview":
    st.title("📘 Retail Sales Analytics Dashboard")
    st.markdown("""
    ### 📌 Project Overview
    This project is a **Data Analytics Dashboard** built for university demonstration using:

    - SQL Server (Star Schema)
    - Advanced SQL Queries
    - Python (Streamlit)

    **Objectives:**
    - Track revenue, orders, average order value
    - Monitor profit and units sold
    - Analyze top-performing products and stores
    """)
    st.markdown("---")
    st.markdown(
    "<b>👤 Developed by:</b> <span style='color:blue; font-weight:600;'>M.Omer Bin Faisal, Mohiuddin, Wasi, Mubasshir</span>",
    unsafe_allow_html=True
)

# ---------------- MAIN DASHBOARD ----------------
elif page == "📊 Main Dashboard":
    st.title("📊 Retail Sales Dashboard Overview")

    # ---------------- KPI DATA ----------------
    revenue = load_data("""
        SELECT SUM(oli.Quantity * p.ProductPrice)
        FROM OrderLineItems oli
        JOIN Products p ON oli.ProductID = p.ProductID;
    """).iloc[0, 0] / 1_000_000

    orders = load_data(
        "SELECT COUNT(DISTINCT OrderNumber) FROM Orders;"
    ).iloc[0, 0]

    aov = load_data("""
        SELECT AVG(OrderRevenue)
        FROM (
            SELECT o.OrderNumber,
                   SUM(oli.Quantity * p.ProductPrice) AS OrderRevenue
            FROM Orders o
            JOIN OrderLineItems oli ON o.OrderNumber = oli.OrderNumber
            JOIN Products p ON oli.ProductID = p.ProductID
            GROUP BY o.OrderNumber
        ) x;
    """).iloc[0, 0]

    # ---------------- KPI CARDS ----------------
    st.markdown("""
    <style>
    .card-wrap { display:flex; gap:12px; margin-bottom:12px; }
    .card {
        background:#f0f2f6;
        border-radius:12px;
        padding:14px;
        flex:1;
        text-align:center;
        box-shadow:1px 1px 5px rgba(0,0,0,0.08);
    }
    .card-title { font-size:15px; font-weight:600; }
    .card-value { font-size:22px; font-weight:bold; color:green; margin-top:6px; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card-wrap">
        <div class="card">
            <div class="card-title">💰 Total Revenue</div>
            <div class="card-value">${revenue:,.2f} M</div>
        </div>
        <div class="card">
            <div class="card-title">🧾 Total Orders</div>
            <div class="card-value">{orders:,}</div>
        </div>
        <div class="card">
            <div class="card-title">📦 Avg Order Value</div>
            <div class="card-value">${aov:,.2f}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ---------------- BAR CHART ----------------
    st.subheader("🏆 Total Profit by Customer State")
    df_bar = load_data("""
        SELECT TOP 6
           c.CustomerState,
           SUM(oli.Quantity * (p.ProductPrice - p.ProductCost)) AS TotalProfit
        FROM Customers c
        JOIN Orders o ON c.CustomerID = o.CustomerID
        JOIN OrderLineItems oli ON o.OrderNumber = oli.OrderNumber
        JOIN Products p ON oli.ProductID = p.ProductID
        GROUP BY c.CustomerState
        ORDER BY TotalProfit DESC;
    """)
    df_bar["TotalProfitM"] = df_bar["TotalProfit"] / 1_000_000

    fig_bar = px.bar(
        df_bar,
        x="CustomerState",
        y="TotalProfitM",
        text=df_bar["TotalProfitM"].map(lambda x: f"{x:,.2f} M"),
        color_discrete_sequence=["#1f77b4"],
        title="<b>Total Profit by Customer State</b>"
    )

    fig_bar.update_traces(
        textposition="inside",
        cliponaxis=False,
        textfont_size=11
    )

    fig_bar.update_layout(
        height=380,
        margin=dict(t=50, b=40, l=40, r=40),
        showlegend=False,
        xaxis=dict(
            title=dict(text="<b>Customer State</b>"),
            tickfont=dict(size=12, family="Arial", color="black")
        ),
        yaxis=dict(
            title=dict(text="<b>Total Profit (Millions)</b>"),
            tickfont=dict(size=12, family="Arial", color="black")
        ),
        font=dict(family="Arial", size=13)
    )

    st.plotly_chart(fig_bar, use_container_width=True)

    # ---------------- DONUT CHART ----------------
    st.subheader("💰 Revenue by Product Category")
    df_donut = load_data("""
        SELECT TOP 5
           c.ProductCategory,
           SUM(oli.Quantity * p.ProductPrice) AS Revenue
        FROM OrderLineItems oli
        JOIN Products p ON oli.ProductID = p.ProductID
        JOIN Subcategories sc ON p.ProductSubcategoryID = sc.ProductSubcategoryID
        JOIN Categories c ON sc.ProductCategoryID = c.ProductCategoryID
        GROUP BY c.ProductCategory
        ORDER BY Revenue DESC;
    """)

    fig_donut = px.pie(
        df_donut,
        names="ProductCategory",
        values="Revenue",
        hole=0.5,
        color_discrete_sequence=px.colors.sequential.Teal,
        title="<b>Revenue by Product Category</b>"
    )

    fig_donut.update_layout(
        height=340,
        margin=dict(t=50, b=40, l=40, r=40),
        font=dict(size=13)
    )

    st.plotly_chart(fig_donut, use_container_width=True)

    # ---------------- DOUBLE LINE CHART ----------------
    st.subheader("📈 Yearly Units Sold & Average Order Value")

    df_line = load_data("""
    WITH YearlyOrderRevenue AS (
       SELECT o.OrderYear,
              o.OrderNumber,
              SUM(oli.Quantity * p.ProductPrice) AS OrderRevenue,
              SUM(oli.Quantity) AS UnitsSold
       FROM Orders o
       JOIN OrderLineItems oli ON o.OrderNumber = oli.OrderNumber
       JOIN Products p ON oli.ProductID = p.ProductID
       GROUP BY o.OrderYear, o.OrderNumber
    ),
    YearlyMetrics AS (
       SELECT OrderYear,
              SUM(UnitsSold) AS TotalUnitsSold,
              AVG(OrderRevenue) AS AvgOrderValue
       FROM YearlyOrderRevenue
       GROUP BY OrderYear
    )
    SELECT * FROM YearlyMetrics
    ORDER BY OrderYear;
    """)

    fig_line = px.line(
        df_line,
        x="OrderYear",
        y="TotalUnitsSold",
        markers=True,
        title="<b>Yearly Units Sold & Average Order Value</b>",
        color_discrete_sequence=["#636EFA"]  # Blue line
    )

    fig_line.add_scatter(
        x=df_line["OrderYear"],
        y=df_line["AvgOrderValue"],
        mode="lines+markers",
        name="Average Order Value",
        line=dict(color="#EF553B", width=3)  # Orange line
    )
    fig_line.update_layout(
        height=380,
        margin=dict(t=50, b=40, l=40, r=40),
        xaxis=dict(title=dict(text="<b>Order Year</b>")),
        yaxis=dict(title=dict(text="<b>Values</b>")),
        font=dict(size=13)
    )

    st.plotly_chart(fig_line, use_container_width=True)


    # ---------------- TABLE ----------------
    st.subheader("🗃️ Store Country & Product Brand Metrics")
    df_table = load_data("""
        SELECT TOP 1000
           s.StoreCountry,
           p.ProductBrand,
           SUM(oli.Quantity) AS UnitsSold,
           SUM(oli.Quantity * p.ProductPrice) AS Revenue,
           SUM(oli.Quantity * (p.ProductPrice - p.ProductCost)) AS Profit
        FROM Orders o
        JOIN Stores s ON o.StoreID = s.StoreID
        JOIN OrderLineItems oli ON o.OrderNumber = oli.OrderNumber
        JOIN Products p ON oli.ProductID = p.ProductID
        GROUP BY s.StoreCountry, p.ProductBrand
        ORDER BY Profit DESC;
    """)
    st.dataframe(df_table, use_container_width=True, height=360)

# ---------------- DATA TABLE TABS ----------------
elif page.startswith(("📄", "🏪", "📦", "📂", "🗂", "📝", "📑")):
    table_mapping = {
        "📄 Customers": "SELECT TOP 1000 * FROM Customers;",
        "🏪 Stores": "SELECT TOP 1000 * FROM Stores;",
        "📦 Products": "SELECT TOP 1000 * FROM Products;",
        "📂 Categories": "SELECT TOP 1000 * FROM Categories;",
        "🗂 Subcategories": "SELECT TOP 1000 * FROM Subcategories;",
        "📝 Orders": "SELECT TOP 1000 * FROM Orders;",
        "📑 Order Line Items": "SELECT TOP 1000 * FROM OrderLineItems;"
    }

    st.subheader(f"📋 {page[2:]} Table Preview")
    df = load_data(table_mapping[page])
    st.dataframe(df, use_container_width=True, height=420)
