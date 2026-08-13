"""
Final Product Price Analysis Report Generator for PricePulse.
"""

from pathlib import Path
from typing import Dict, Any
from pricepulse.models import Product
from pricepulse.analyzer import PriceAnalyzer
from pricepulse.visualizer import PriceVisualizer
from pricepulse.logger import setup_logger

logger = setup_logger("ReportGenerator")


class ReportGenerator:
    """Generates structured Markdown and HTML price analysis reports."""

    def __init__(self, product: Product):
        self.product = product
        self.analyzer = PriceAnalyzer(product)
        self.visualizer = PriceVisualizer(product)

    def generate_report(self, output_dir: str = "output") -> Dict[str, str]:
        """
        Generates full analysis report and chart visualization.
        Returns paths to generated markdown, html, and image files.
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        # 1. Generate chart image
        chart_path = self.visualizer.plot_10_year_trend(output_dir=output_dir)
        interactive_path = self.visualizer.generate_interactive_plotly(output_dir=output_dir)

        # 2. Gather analytics & recommendation
        stats = self.analyzer.get_summary_statistics()
        rec = self.analyzer.get_buying_recommendation()
        drops = self.analyzer.detect_price_drops()

        curr = self.product.currency

        # 3. Build Markdown content
        md_content = f"""# 📊 PricePulse Product Price Analysis Report

**Product:** {self.product.title}  
**Product ID:** `{self.product.product_id}`  
**Category:** {self.product.category} | **Brand:** {self.product.brand}  
**Google Search Source:** [{self.product.url}]({self.product.url})  

---

## 💰 Current Price Overview
- **Latest Recorded Price:** `{curr} {stats['current_price']:,.2f}`
- **Previous Price Point:** `{curr} {stats['previous_price']:,.2f}`
- **Recent Price Change:** `{stats['price_change_abs']:+,.2f} ({stats['price_change_pct']:+.2f}%)`
- **User Target Price:** `{curr} {self.product.target_price if self.product.target_price else 'Not Set'}`

---

## 📈 10-Year Historical Trend Analysis (2016–2026)
- **10-Year All-Time Low (ATL):** `{curr} {stats['all_time_low']:,.2f}` *(Recorded on {stats['atl_date']})*
- **10-Year All-Time High (ATH):** `{curr} {stats['all_time_high']:,.2f}` *(Recorded on {stats['ath_date']})*
- **10-Year Mean Price:** `{curr} {stats['mean_10y_price']:,.2f}`
- **1-Year Moving Average:** `{curr} {stats['mean_1y_price']:,.2f}`
- **Current Price vs. 1-Year Average:** `{stats['avg_1y_diff_pct']:+.2f}%`

---

## 💡 Purchasing Opportunity & Recommendation

### 🏷️ Overall Rating: **{rec['rating']}** (Deal Score: `{rec['score']}/100`)

#### Key Insights & Reasoning:
"""
        for point in rec['reasoning']:
            md_content += f"- {point}\n"

        md_content += f"\n#### 🗓️ Best Time to Buy Advice:\n> {rec['seasonal_advice']}\n\n---\n"

        # Price Drops Table
        md_content += "## 📉 Notable Historical Price Drops\n\n"
        if drops:
            md_content += "| Date | Old Price | New Price | Drop Amount | Drop % | Event / Note |\n"
            md_content += "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            for d in drops[-10:]:  # Show top recent 10 drops
                md_content += f"| {d['date']} | {curr} {d['old_price']:,.2f} | {curr} {d['new_price']:,.2f} | -{curr} {d['drop_amount']:,.2f} | -{d['drop_percent']:.1f}% | {d['notes']} |\n"
        else:
            md_content += "*No major price drops recorded in price history timeline.*\n"

        md_content += f"\n---\n\n![10-Year Trend Chart](file:///{Path(chart_path).resolve().as_posix()})\n"

        # Save Markdown File
        md_file = out_path / f"report_{self.product.product_id}.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_content)

        logger.info(f"Generated Markdown report: {md_file}")

        return {
            "markdown": str(md_file),
            "chart_image": chart_path,
            "interactive_html": interactive_path or "",
            "summary": rec
        }
