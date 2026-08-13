"""
PricePulse - Command Line Interface (CLI) Main Entry Point.
"""

import sys
import os
import subprocess
from pathlib import Path

# Fix Windows console UTF-8 printing
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from pricepulse.models import Product
from pricepulse.storage import StorageManager
from pricepulse.google_api import GooglePriceFetcher
from pricepulse.analyzer import PriceAnalyzer
from pricepulse.visualizer import PriceVisualizer
from pricepulse.report_generator import ReportGenerator
from pricepulse.logger import setup_logger

logger = setup_logger("CLI")
storage = StorageManager()
google_fetcher = GooglePriceFetcher()


def print_banner():
    print("=" * 70)
    print("                🚀 PricePulse Tracking & Analysis System")
    print("        10-Year Product Price Trend Analyzer & Buying Advisor")
    print("=" * 70)


def handle_search_product():
    print("\n🔍 --- Search Product & Fetch 10-Year Google Price Data ---")
    query = input("Enter product name (e.g. 'iPhone 15 Pro', 'Sony WH-1000XM5', 'MacBook Air'): ").strip()
    if not query:
        print("❌ Search query cannot be empty.")
        return

    print(f"\n📡 Connecting to Google API & generating 10-year historical dataset for '{query}'...")
    try:
        product = google_fetcher.search_and_build_product(query)
        storage.save_product(product)

        # Run analysis
        analyzer = PriceAnalyzer(product)
        stats = analyzer.get_summary_statistics()
        rec = analyzer.get_buying_recommendation()
        drops = analyzer.detect_price_drops()

        # Generate report and chart
        reporter = ReportGenerator(product)
        report_data = reporter.generate_report()

        print("\n" + "=" * 65)
        print(f"📦 Product Identified: {product.title}")
        print(f"💰 Current Price (Google Source): {product.currency} {stats['current_price']:,.2f}")
        print(f"📉 10-Year All-Time Low (ATL): {product.currency} {stats['all_time_low']:,.2f} ({stats['atl_date']})")
        print(f"📈 10-Year All-Time High (ATH): {product.currency} {stats['all_time_high']:,.2f} ({stats['ath_date']})")
        print(f"📊 10-Year Mean Price: {product.currency} {stats['mean_10y_price']:,.2f}")
        print(f"📅 1-Year Moving Average: {product.currency} {stats['mean_1y_price']:,.2f}")
        print("=" * 65)

        print(f"\n💡 BUYING RECOMMENDATION: [{rec['rating']}] (Deal Score: {rec['score']}/100)")
        print("   Reasoning:")
        for r in rec["reasoning"]:
            print(f"   • {r}")
        print(f"\n   🗓️ Best Time to Buy: {rec['seasonal_advice']}")

        if drops:
            latest_drop = drops[-1]
            print(f"\n📉 Latest Price Drop Recorded: -{product.currency} {latest_drop['drop_amount']} (-{latest_drop['drop_percent']}%) on {latest_drop['date']}")

        print(f"\n🖼️  10-Year Chart Saved To: {report_data['chart_image']}")
        print(f"📝 Full Report Saved To: {report_data['markdown']}")
        print("=" * 65)

    except Exception as e:
        logger.error(f"Error during search: {e}")
        print(f"❌ Failed to search/analyze product: {e}")


def handle_view_saved():
    print("\n📦 --- Saved Products in Database ---")
    products = storage.list_products()
    if not products:
        print("No products currently stored in database.")
        return

    print(f"{'ID':<25} | {'Title':<30} | {'Current Price':<15} | {'History Points'}")
    print("-" * 80)
    for p in products:
        print(f"{p.product_id:<25} | {p.title[:28]:<30} | {p.currency} {p.current_price:<10.2f} | {len(p.price_history)}")


def handle_generate_graph():
    print("\n📊 --- Generate Graph for Saved Product ---")
    query = input("Enter stored product ID or title keyword: ").strip()
    product = storage.find_product_by_query(query)
    if not product:
        print(f"❌ Product matching '{query}' not found in saved database.")
        return

    try:
        vis = PriceVisualizer(product)
        path = vis.plot_10_year_trend(show=True)
        print(f"✅ Chart displayed and saved to: {path}")
    except Exception as e:
        print(f"❌ Error generating chart: {e}")


def handle_export_csv():
    print("\n📁 --- Export Product Price History to CSV ---")
    query = input("Enter product ID or title: ").strip()
    product = storage.find_product_by_query(query)
    if not product:
        print(f"❌ Product matching '{query}' not found.")
        return

    out_file = f"output/{product.product_id}_history.csv"
    try:
        storage.export_to_csv(product.product_id, out_file)
        print(f"✅ CSV Export successful: {out_file}")
    except Exception as e:
        print(f"❌ Export failed: {e}")


def handle_launch_webapp():
    print("\n🌐 Launching Streamlit PricePulse Web Dashboard...")
    print("The web server will open in your browser shortly. Press Ctrl+C in terminal to stop.")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    except Exception as e:
        print(f"❌ Failed to launch Streamlit: {e}")


def main_menu():
    print_banner()
    while True:
        print("\nMain Menu:")
        print("  1. Search Product Name & Generate 10-Year Price Trend + Analysis")
        print("  2. View Saved Products Database")
        print("  3. View & Display 10-Year Price Chart for Saved Product")
        print("  4. Export Price History to CSV")
        print("  5. Launch Interactive Web App Dashboard (Streamlit)")
        print("  6. Exit")

        choice = input("\nSelect an option (1-6): ").strip()

        if choice == "1":
            handle_search_product()
     
        elif choice == "2":
            handle_view_saved()
        
        elif choice == "3":
            handle_generate_graph()
        
        elif choice == "4":
            handle_export_csv()
           
        elif choice == "5":
            handle_launch_webapp()
            
        elif choice == "6":
            print("\nThank you for using PricePulse! Goodbye. 👋")
            break
        else:
            print("Invalid choice. Please enter a number from 1 to 6.")


if __name__ == "__main__":
    main_menu()
