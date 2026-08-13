"""
PricePulse - Streamlit Interactive Web Application.
"""

import streamlit as st
import pandas as pd
from pathlib import Path

from pricepulse.storage import StorageManager
from pricepulse.google_api import GooglePriceFetcher
from pricepulse.analyzer import PriceAnalyzer
from pricepulse.visualizer import PriceVisualizer
from pricepulse.report_generator import ReportGenerator

# Page configuration
st.set_page_config(
    page_title="PricePulse - Product Price Tracker & 10-Year Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for high-contrast, modern dark UI aesthetics
st.markdown("""
<style>
    /* Force main container dark background */
    .stApp, [data-testid="stAppViewContainer"], .main {
        background-color: #0f172a !important;
        color: #f8fafc !important;
        font-family: 'Segoe UI', Roboto, sans-serif !important;
    }
    
    header[data-testid="stHeader"] {
        background-color: #0f172a !important;
    }
    
    /* Force sidebar dark background */
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div {
        background-color: #1e293b !important;
    }
    
    /* All Headings: Bright White & Bold */
    h1, h2, h3, h4, h5, h6, [data-testid="stHeader"] h1 {
        color: #ffffff !important;
        font-weight: 800 !important;
        letter-spacing: 0.5px;
    }
    
    /* All text paragraphs and markdown */
    p, span, label, li, .stMarkdownContainer p {
        color: #e2e8f0 !important;
        font-weight: 600 !important;
    }

    /* Metric Cards styling */
    [data-testid="stMetric"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        padding: 15px !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3) !important;
    }
    [data-testid="stMetricLabel"] p, [data-testid="stMetricLabel"] label {
        color: #94a3b8 !important;
        font-size: 15px !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetricValue"] div {
        color: #38bdf8 !important;
        font-size: 26px !important;
        font-weight: 800 !important;
    }

    /* Input Field Labels & Text box */
    .stTextInput label, div[data-baseweb="input"] label {
        color: #38bdf8 !important;
        font-size: 18px !important;
        font-weight: 800 !important;
    }

    .stTextInput input, div[data-baseweb="input"] input {
        color: #ffffff !important;
        background-color: #1e293b !important;
        font-size: 18px !important;
        font-weight: bold !important;
        border: 2px solid #3b82f6 !important;
        border-radius: 8px !important;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 16px !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
    }

    /* Selectbox dropdowns */
    div[data-baseweb="select"] > div {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid #3b82f6 !important;
    }

    /* Cards */
    .card {
        background: #1e293b;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        margin-bottom: 20px;
        border: 2px solid #334155;
    }

    /* Recommendation Badges */
    .badge-buy {
        background: #10b981; color: #ffffff !important; padding: 8px 18px;
        border-radius: 20px; font-weight: 800; font-size: 18px;
        display: inline-block; box-shadow: 0 2px 8px rgba(16,185,129,0.4);
    }
    .badge-hold {
        background: #f59e0b; color: #ffffff !important; padding: 8px 18px;
        border-radius: 20px; font-weight: 800; font-size: 18px;
        display: inline-block; box-shadow: 0 2px 8px rgba(245,158,11,0.4);
    }
    .badge-overpriced {
        background: #ef4444; color: #ffffff !important; padding: 8px 18px;
        border-radius: 20px; font-weight: 800; font-size: 18px;
        display: inline-block; box-shadow: 0 2px 8px rgba(239,68,68,0.4);
    }
</style>
""", unsafe_allow_html=True)

# Initialize singletons
storage = StorageManager()
fetcher = GooglePriceFetcher()


def render_sidebar():
    st.sidebar.title("🚀 PricePulse Navigation")
    st.sidebar.markdown("---")
    
    saved_prods = storage.list_products()
    st.sidebar.subheader(f"📦 Stored Products ({len(saved_prods)})")
    
    if saved_prods:
        options = ["-- New Search --"] + [f"{p.title} ({p.currency}{p.current_price})" for p in saved_prods]
        
        def on_sidebar_select():
            choice = st.session_state.get("sidebar_select_option")
            if choice and choice != "-- New Search --":
                idx = options.index(choice) - 1
                selected_prod = saved_prods[idx]
                st.session_state["active_product"] = selected_prod
                st.session_state["last_query"] = selected_prod.title
                st.session_state["query_input_text"] = selected_prod.title

        st.sidebar.selectbox(
            "Select Stored Product:",
            options,
            key="sidebar_select_option",
            on_change=on_sidebar_select
        )

    st.sidebar.markdown("---")
    st.sidebar.info("""
    **PricePulse Features:**
    - 🔍 Search Any Product
    - 📈 10-Year Historical Price Trend
    - 💡 Smart Buying Recommendation
    - 📉 Historical Price Drop Alerts
    - 📄 Export CSV & Markdown Reports
    """)


def main():
    st.title("📈 PricePulse - Product Price Tracker & 10-Year Trend Analyzer")
    st.caption("Monitors product prices, connects with Google APIs, analyzes 10-year historical trends, and delivers data-driven purchase advice.")

    render_sidebar()

    # Default query state initialization
    if "query_input_text" not in st.session_state:
        st.session_state["query_input_text"] = "Sony WH-1000XM5"

    # Search Bar
    st.markdown("### 🔍 Track New Product")
    col1, col2 = st.columns([4, 1])
    with col1:
        query_input = st.text_input(
            "Enter any Product Name:",
            value=st.session_state["query_input_text"],
            placeholder="e.g. iPhone 15 Pro, PlayStation 5, MacBook Air M2, Nike Air Max"
        )
    with col2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        search_btn = st.button("🚀 Analyze Price", use_container_width=True)

    query = query_input.strip()

    # Determine if a new query needs to be fetched & processed
    needs_fetch = False
    if search_btn:
        needs_fetch = True
    elif "active_product" not in st.session_state:
        needs_fetch = True
    elif query and st.session_state.get("last_query") != query:
        needs_fetch = True

    if needs_fetch and query:
        with st.spinner(f"Connecting to Google API & synthesizing 10-year historical data for '{query}'..."):
            product = fetcher.search_and_build_product(query)
            storage.save_product(product)
            st.session_state["active_product"] = product
            st.session_state["last_query"] = query
            st.session_state["query_input_text"] = query

    if "active_product" in st.session_state:
        product = st.session_state["active_product"]

        # Run Analysis
        analyzer = PriceAnalyzer(product)
        stats = analyzer.get_summary_statistics()
        rec = analyzer.get_buying_recommendation()
        drops = analyzer.detect_price_drops()
        curr = product.currency

        st.markdown("---")

        # Top Header Info
        st.header(f"📦 {product.title}")
        st.markdown(f"**Category:** {product.category} | **Brand:** {product.brand} | **Google Search:** [{product.url}]({product.url})")

        # Metric Cards Row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(
            label="Current Price",
            value=f"{curr} {stats['current_price']:,.2f}",
            delta=f"{stats['price_change_pct']:+.2f}%",
            delta_color="inverse"
        )
        m2.metric(
            label="10-Yr All-Time Low (ATL)",
            value=f"{curr} {stats['all_time_low']:,.2f}",
            help=f"Recorded on {stats['atl_date']}"
        )
        m3.metric(
            label="10-Yr All-Time High (ATH)",
            value=f"{curr} {stats['all_time_high']:,.2f}",
            help=f"Recorded on {stats['ath_date']}"
        )
        m4.metric(
            label="1-Year Average Price",
            value=f"{curr} {stats['mean_1y_price']:,.2f}",
            delta=f"{stats['avg_1y_diff_pct']:+.2f}% vs Avg",
            delta_color="inverse"
        )

        st.markdown("---")

        # Visualizations & Recommendation layout
        col_left, col_right = st.columns([2.2, 1])

        with col_left:
            st.subheader("📊 10-Year Price Trend Chart (2016–2026)")
            
            # Render Matplotlib PNG chart
            vis = PriceVisualizer(product)
            chart_file = vis.plot_10_year_trend()
            st.image(chart_file, use_column_width=True)

            # Interactive Plotly option
            with st.expander("🌐 View Interactive Zoomable Graph"):
                df = analyzer.df
                st.line_chart(df.set_index("date")[["price", "ma_365"]])

        with col_right:
            st.subheader("💡 Purchasing Advice")
            
            # Recommendation Badge
            rating_text = rec["rating"]
            if "BUY" in rating_text or "GREAT" in rating_text:
                badge_class = "badge-buy"
            elif "OVERPRICED" in rating_text or "HIGH" in rating_text or "PEAK" in rating_text:
                badge_class = "badge-overpriced"
            else:
                badge_class = "badge-hold"

            st.markdown(f"#### Recommendation:\n<span class='{badge_class}'>{rating_text}</span>", unsafe_allow_html=True)
            st.markdown(f"<br>**Deal Score:** `{rec['score']} / 100`", unsafe_allow_html=True)

            st.progress(rec['score'] / 100)

            st.markdown("#### Key Insights:")
            for reason in rec["reasoning"]:
                st.write(f"- {reason}")

            st.markdown("#### 🗓️ Best Time to Buy:")
            st.info(rec["seasonal_advice"])

            # Report Download
            reporter = ReportGenerator(product)
            rep_data = reporter.generate_report()
            with open(rep_data["markdown"], "r", encoding="utf-8") as f:
                md_text = f.read()
            
            st.download_button(
                label="📥 Download Full Price Report (.md)",
                data=md_text,
                file_name=f"PricePulse_Report_{product.product_id}.md",
                mime="text/markdown"
            )

        # Price Drops Table
        st.markdown("---")
        st.subheader("📉 Historical Price Drop Events")
        if drops:
            drop_df = pd.DataFrame(drops)
            drop_df["old_price"] = drop_df["old_price"].apply(lambda x: f"{curr} {x:,.2f}")
            drop_df["new_price"] = drop_df["new_price"].apply(lambda x: f"{curr} {x:,.2f}")
            drop_df["drop_amount"] = drop_df["drop_amount"].apply(lambda x: f"-{curr} {x:,.2f}")
            drop_df["drop_percent"] = drop_df["drop_percent"].apply(lambda x: f"-{x:.1f}%")

            st.dataframe(
                drop_df.rename(columns={
                    "date": "Date", "old_price": "Previous Price", "new_price": "Price After Drop",
                    "drop_amount": "Price Cut Amount", "drop_percent": "Discount %", "notes": "Event Note"
                }),
                use_container_width=True
            )
        else:
            st.write("No major price drop events recorded.")


if __name__ == "__main__":
    main()
