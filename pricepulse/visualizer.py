"""
Data Visualization Engine for PricePulse using Matplotlib & Plotly.
"""

from pathlib import Path
from typing import Optional
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

from pricepulse.models import Product
from pricepulse.analyzer import PriceAnalyzer
from pricepulse.logger import setup_logger
from pricepulse.exceptions import ReportGenerationError

logger = setup_logger("Visualizer")


class PriceVisualizer:
    """Generates high-resolution dark-mode charts and interactive visual reports."""

    def __init__(self, product: Product):
        self.product = product
        self.analyzer = PriceAnalyzer(product)
        self.df = self.analyzer.df

    def plot_10_year_trend(self, output_dir: str = "output", show: bool = False) -> str:
        """
        Creates a dark-theme 10-year price history chart with moving averages,
        All-Time Low markers, All-Time High markers, and saves it as PNG.
        """
        if self.df.empty:
            raise ReportGenerationError("Cannot plot chart for empty price history.")

        output_path = Path(output_dir) / f"trend_{self.product.product_id}.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        stats = self.analyzer.get_summary_statistics()
        curr_symbol = self.product.currency

        # Styling
        plt.clf()
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(12, 6.5), dpi=150)
        fig.patch.set_facecolor('#0f172a')
        ax.set_facecolor('#1e293b')

        # Plot main price trend line
        ax.plot(self.df["date"], self.df["price"], color='#38bdf8', linewidth=3.0, label='Price History (10-Yr)', zorder=3)

        # Plot 1-Year Moving Average (365d)
        if "ma_365" in self.df and not self.df["ma_365"].isna().all():
            ax.plot(self.df["date"], self.df["ma_365"], color='#f59e0b', linestyle='--', linewidth=2.2, label='1-Year Moving Avg', zorder=2)

        # Target Price Line if set
        if self.product.target_price:
            ax.axhline(y=self.product.target_price, color='#a855f7', linestyle=':', linewidth=2.0, label=f'Target Price ({curr_symbol} {self.product.target_price:,.2f})', zorder=2)

        # Mark All Time Low (ATL)
        min_idx = self.df["price"].idxmin()
        atl_row = self.df.loc[min_idx]
        ax.scatter(atl_row["date"], atl_row["price"], color='#10b981', s=160, zorder=5, marker='*', label=f'All-Time Low ({curr_symbol} {atl_row["price"]:,.2f})')
        ax.annotate(
            f" ALL-TIME LOW: {curr_symbol} {atl_row['price']:,.2f}\n ({atl_row['date'].strftime('%b %Y')})",
            (atl_row["date"], atl_row["price"]),
            textcoords="offset points", xytext=(0, -32), ha='center',
            bbox=dict(boxstyle="round,pad=0.5", fc="#022c22", ec="#10b981", lw=2),
            color="#34d399", fontsize=10, fontweight='bold'
        )

        # Mark All Time High (ATH)
        max_idx = self.df["price"].idxmax()
        ath_row = self.df.loc[max_idx]
        ax.scatter(ath_row["date"], ath_row["price"], color='#ef4444', s=140, zorder=5, marker='^', label=f'All-Time High ({curr_symbol} {ath_row["price"]:,.2f})')
        ax.annotate(
            f" ATH: {curr_symbol} {ath_row['price']:,.2f}\n ({ath_row['date'].strftime('%b %Y')})",
            (ath_row["date"], ath_row["price"]),
            textcoords="offset points", xytext=(0, 20), ha='center',
            bbox=dict(boxstyle="round,pad=0.4", fc="#450a0a", ec="#ef4444", lw=1.5),
            color="#fca5a5", fontsize=9, fontweight='bold'
        )

        # Mark Latest Price Point
        latest_row = self.df.iloc[-1]
        ax.scatter(latest_row["date"], latest_row["price"], color='#38bdf8', s=120, zorder=5, marker='o')
        ax.annotate(
            f" Current: {curr_symbol} {latest_row['price']:,.2f}",
            (latest_row["date"], latest_row["price"]),
            textcoords="offset points", xytext=(-25, -25),
            bbox=dict(boxstyle="round,pad=0.5", fc="#0f172a", ec="#38bdf8", lw=2),
            color="#ffffff", fontsize=10, fontweight='bold'
        )

        # Formatting axes & high-contrast bold titles
        ax.set_title(f"PricePulse 10-Year Price Trend (Low-to-High): {self.product.title}", fontsize=16, fontweight='bold', color='#ffffff', pad=20, bbox=dict(boxstyle="round,pad=0.4", fc="#1e293b", ec="#3b82f6", lw=1.5))
        ax.set_xlabel("Date (Year)", fontsize=12, fontweight='bold', color='#ffffff', labelpad=12)
        ax.set_ylabel(f"Price in Indian Rupees ({curr_symbol})", fontsize=12, fontweight='bold', color='#ffffff', labelpad=12)
        
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.xaxis.set_major_locator(mdates.YearLocator())
        plt.xticks(rotation=0, color='#ffffff', fontsize=10, fontweight='bold')
        plt.yticks(color='#ffffff', fontsize=10, fontweight='bold')

        ax.grid(True, linestyle=':', alpha=0.4, color='#64748b')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#64748b')
        ax.spines['bottom'].set_color('#64748b')

        legend = ax.legend(loc='upper left', facecolor='#0f172a', edgecolor='#3b82f6', labelcolor='#ffffff', fontsize=10, framealpha=0.95)
        for text in legend.get_texts():
            text.set_fontweight('bold')

        plt.tight_layout()

        fig.savefig(output_path, facecolor=fig.get_facecolor(), edgecolor='none')
        if show:
            plt.show()
        plt.close('all')

        logger.info(f"Generated plot chart: {output_path}")
        return str(output_path)

    def generate_interactive_plotly(self, output_dir: str = "output") -> Optional[str]:
        """Generates an interactive Plotly HTML 10-year chart."""
        try:
            import plotly.graph_objects as go

            fig = go.Figure()
            
            # Price line
            fig.add_trace(go.Scatter(
                x=self.df["date"],
                y=self.df["price"],
                mode='lines+markers',
                name='Price History',
                line=dict(color='#89b4fa', width=2.5),
                marker=dict(size=4)
            ))

            # 1-Year MA
            if "ma_365" in self.df:
                fig.add_trace(go.Scatter(
                    x=self.df["date"],
                    y=self.df["ma_365"],
                    mode='lines',
                    name='1-Year Moving Avg',
                    line=dict(color='#f9e2af', width=2, dash='dash')
                ))

            fig.update_layout(
                title=f"PricePulse Interactive 10-Year Trend: {self.product.title}",
                template="plotly_dark",
                xaxis_title="Date",
                yaxis_title=f"Price ({self.product.currency})",
                paper_bgcolor="#11111b",
                plot_bgcolor="#181825",
                font=dict(color="#cdd6f4")
            )

            html_path = Path(output_dir) / f"interactive_{self.product.product_id}.html"
            html_path.parent.mkdir(parents=True, exist_ok=True)
            fig.write_html(str(html_path))
            return str(html_path)
        except ImportError:
            logger.warning("Plotly not available for interactive HTML export.")
            return None
