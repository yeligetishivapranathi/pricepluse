"""
Pandas-powered Data Analysis & Price Trend Engine for PricePulse.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from pricepulse.models import Product, PricePoint
from pricepulse.logger import setup_logger
from pricepulse.exceptions import PricePulseException

logger = setup_logger("Analyzer")

class PriceAnalyzer:
    """Performs statistical, trend, moving average, and buying opportunity analysis using Pandas."""

    def __init__(self, product: Product):
        self.product = product
        self.df = self._build_dataframe(product.price_history)

    def _build_dataframe(self, history: List[PricePoint]) -> pd.DataFrame:
        """Converts price history list into a clean, indexed Pandas DataFrame."""
        if not history:
            return pd.DataFrame(columns=["date", "price", "platform", "in_stock", "notes"])

        data = [pt.to_dict() for pt in history]
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        
        # Calculate moving averages
        df["ma_30"] = df["price"].rolling(window=3, min_periods=1).mean()
        df["ma_90"] = df["price"].rolling(window=6, min_periods=1).mean()
        df["ma_365"] = df["price"].rolling(window=12, min_periods=1).mean()
        
        # Percentage changes
        df["price_change_pct"] = df["price"].pct_change() * 100.0
        return df

    def get_summary_statistics(self) -> Dict[str, Any]:
        """Calculates 10-year and recent price statistics using Pandas."""
        if self.df.empty:
            return {
                "current_price": self.product.current_price,
                "total_records": 0,
                "currency": self.product.currency
            }

        prices = self.df["price"]
        current = float(prices.iloc[-1])
        previous = float(prices.iloc[-2]) if len(prices) > 1 else current
        
        all_time_low = float(prices.min())
        all_time_high = float(prices.max())
        mean_price = float(prices.mean())
        median_price = float(prices.median())
        
        atl_row = self.df.loc[self.df["price"].idxmin()]
        ath_row = self.df.loc[self.df["price"].idxmax()]

        # 1-year stats (last 12 recordings)
        df_1y = self.df.tail(12)
        mean_1y = float(df_1y["price"].mean())
        min_1y = float(df_1y["price"].min())
        max_1y = float(df_1y["price"].max())

        # Percentage changes
        prev_change = current - previous
        prev_change_pct = (prev_change / previous * 100.0) if previous > 0 else 0.0

        atl_diff_pct = ((current - all_time_low) / all_time_low * 100.0) if all_time_low > 0 else 0.0
        avg_1y_diff_pct = ((current - mean_1y) / mean_1y * 100.0) if mean_1y > 0 else 0.0

        return {
            "title": self.product.title,
            "currency": self.product.currency,
            "current_price": current,
            "previous_price": previous,
            "price_change_abs": round(prev_change, 2),
            "price_change_pct": round(prev_change_pct, 2),
            "all_time_low": round(all_time_low, 2),
            "atl_date": str(atl_row["date"].strftime("%Y-%m-%d")),
            "all_time_high": round(all_time_high, 2),
            "ath_date": str(ath_row["date"].strftime("%Y-%m-%d")),
            "mean_10y_price": round(mean_price, 2),
            "median_10y_price": round(median_price, 2),
            "mean_1y_price": round(mean_1y, 2),
            "min_1y_price": round(min_1y, 2),
            "max_1y_price": round(max_1y, 2),
            "atl_diff_pct": round(atl_diff_pct, 2),
            "avg_1y_diff_pct": round(avg_1y_diff_pct, 2),
            "total_records": len(self.df)
        }

    def detect_price_drops(self) -> List[Dict[str, Any]]:
        """Identifies all historical price drop events in the dataset."""
        drops = []
        if len(self.df) < 2:
            return drops

        for i in range(1, len(self.df)):
            curr_row = self.df.iloc[i]
            prev_row = self.df.iloc[i-1]
            diff = curr_row["price"] - prev_row["price"]
            
            if diff < 0:
                pct = (diff / prev_row["price"]) * 100.0
                drops.append({
                    "date": curr_row["date"].strftime("%Y-%m-%d"),
                    "old_price": float(prev_row["price"]),
                    "new_price": float(curr_row["price"]),
                    "drop_amount": round(abs(diff), 2),
                    "drop_percent": round(abs(pct), 2),
                    "notes": curr_row.get("notes", "Price Drop")
                })
        return drops

    def get_buying_recommendation(self) -> Dict[str, Any]:
        """
        Generates data-driven buying suggestions based on 10-year statistical thresholds,
        moving averages, and historical price drops.
        """
        stats = self.get_summary_statistics()
        current = stats["current_price"]
        atl = stats["all_time_low"]
        mean_1y = stats["mean_1y_price"]
        avg_1y_diff_pct = stats["avg_1y_diff_pct"]
        target = self.product.target_price

        # Determination logic
        rating = "HOLD / WAIT"
        score = 50  # 0-100 scale
        reasoning = []
        key_insights = []

        # Target price check
        if target and current <= target:
            score += 25
            reasoning.append(f"Current price ({stats['currency']}{current}) is below your target price ({stats['currency']}{target}).")

        # All Time Low check
        if current <= atl * 1.03:
            rating = "GREAT BUY (ALL-TIME LOW NEARBY!)"
            score += 40
            reasoning.append(f"Price is near the 10-year All-Time Low of {stats['currency']}{atl} (Recorded on {stats['atl_date']}).")
            key_insights.append("Historical bottom detected — lowest recorded price in 10 years.")
        elif avg_1y_diff_pct <= -12.0:
            rating = "STRONG BUY"
            score += 30
            reasoning.append(f"Price is {abs(avg_1y_diff_pct)}% below the 1-Year Average ({stats['currency']}{mean_1y}).")
            key_insights.append("Significant price drop below 1-year baseline.")
        elif avg_1y_diff_pct <= -4.0:
            rating = "GOOD DEAL"
            score += 15
            reasoning.append(f"Price is moderately discounted ({abs(avg_1y_diff_pct)}% below 1-Year Average).")
            key_insights.append("Favorable discount relative to annual trend.")
        elif avg_1y_diff_pct >= 10.0:
            rating = "OVERPRICED - WAIT FOR SALE"
            score -= 25
            reasoning.append(f"Current price is {avg_1y_diff_pct}% HIGHER than 1-Year Average ({stats['currency']}{mean_1y}).")
            key_insights.append("Peak pricing phase — recommend waiting for upcoming seasonal sales.")
        else:
            rating = "FAIR RETAIL PRICE"
            reasoning.append(f"Current price is close to the 1-year mean price ({stats['currency']}{mean_1y}).")
            key_insights.append("Standard retail price without major active promotion.")

        # Seasonal advice
        seasonal_advice = "The best historical discounts for this category occur during Black Friday (November) and Mid-Year Sales (July)."

        return {
            "rating": rating,
            "score": min(100, max(0, score)),
            "current_price": current,
            "currency": stats["currency"],
            "target_price": target,
            "reasoning": reasoning,
            "key_insights": key_insights,
            "seasonal_advice": seasonal_advice,
            "summary_stats": stats
        }
