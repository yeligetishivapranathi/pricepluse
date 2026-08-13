"""
PricePulse - Standalone Item Graph Generator.
Usage:
  python generate_graph.py "Item Name"
Or run directly and enter any item name when prompted.
"""

import sys
import os
import argparse
from pathlib import Path

# Fix Windows console UTF-8 printing
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from pricepulse.google_api import GooglePriceFetcher
from pricepulse.storage import StorageManager
from pricepulse.analyzer import PriceAnalyzer
from pricepulse.visualizer import PriceVisualizer
from pricepulse.report_generator import ReportGenerator
from pricepulse.logger import setup_logger

logger = setup_logger("GraphGenerator")

def generate_graph_for_item(item_name: str, show_image: bool = True):
    """
    Generates 10-year price trend graph, analysis, and report for any input item name.
    """
    print("=" * 70)
    print(f" 📈 Generating 10-Year Price Trend Graph for: '{item_name}'")
    print("=" * 70)

    fetcher = GooglePriceFetcher()
    storage = StorageManager()

    # 1. Fetch price info & generate 10-year historical dataset
    print(f"📡 Querying Google API & building 10-year dataset in Indian Rupees (₹)...")
    product = fetcher.search_and_build_product(item_name)
    storage.save_product(product)

    # 2. Run analysis
    analyzer = PriceAnalyzer(product)
    stats = analyzer.get_summary_statistics()
    rec = analyzer.get_buying_recommendation()
    drops = analyzer.detect_price_drops()

    # 3. Generate chart image and report
    reporter = ReportGenerator(product)
    report_data = reporter.generate_report()
    chart_path = report_data["chart_image"]

    curr = product.currency

    print("\n" + "─" * 65)
    print(f"📦 Product Name:  {product.title}")
    print(f"💰 Current Price: {curr} {stats['current_price']:,.2f}")
    print(f"📉 10-Yr Low (ATL): {curr} {stats['all_time_low']:,.2f} (Recorded: {stats['atl_date']})")
    print(f"📈 10-Yr High (ATH): {curr} {stats['all_time_high']:,.2f} (Recorded: {stats['ath_date']})")
    print(f"📅 1-Yr Average:  {curr} {stats['mean_1y_price']:,.2f}")
    print("─" * 65)

    print(f"\n💡 BUYING ADVICE: [{rec['rating']}] (Deal Score: {rec['score']}/100)")
    for r in rec["reasoning"]:
        print(f"   • {r}")
    print(f"   🗓️ Best Season to Buy: {rec['seasonal_advice']}")

    if drops:
        latest_drop = drops[-1]
        print(f"\n📉 Recent Price Cut: -{curr} {latest_drop['drop_amount']:,.2f} (-{latest_drop['drop_percent']}%) on {latest_drop['date']}")

    print("\n" + "─" * 65)
    print(f"🖼️  Graph PNG Image Generated: {Path(chart_path).resolve()}")
    print(f"📝 Full Report Saved To:      {Path(report_data['markdown']).resolve()}")
    print("─" * 65)

    # 4. Open/Display PNG image automatically on Windows
    if show_image and os.name == 'nt':
        try:
            print("🚀 Opening graph image in your default image viewer...")
            os.startfile(Path(chart_path).resolve())
        except Exception as e:
            logger.warning(f"Could not automatically open image viewer: {e}")

    return chart_path


if __name__ == "__main__":
    if len(sys.argv) > 1:
        query_item = " ".join(sys.argv[1:])
    else:
        query_item = input("\nEnter any Product / Item Name (e.g. 'iPhone 15 Pro', 'Nike Air Max', 'Sony Headphones'): ").strip()
    
    if not query_item:
        query_item = "iPhone 15 Pro"
        print("No item name entered. Defaulting to 'iPhone 15 Pro'.")

    generate_graph_for_item(query_item)
