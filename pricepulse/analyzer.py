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
            "latest_date": str(self.df.iloc[-1]["date"].strftime("%Y-%m-%d")),
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

    def _calculate_best_buying_months(self) -> str:
        """
        Analyzes 10-year monthly historical price trends for this specific product,
        finds empirical lowest-price calendar months, and combines them with category intelligence.
        """
        months_map = {
            1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
            7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"
        }
        
        empirical_note = ""
        if not self.df.empty and len(self.df) >= 12:
            df_copy = self.df.copy()
            df_copy["month_num"] = df_copy["date"].dt.month
            monthly_means = df_copy.groupby("month_num")["price"].mean()
            sorted_months = monthly_means.sort_values().index.tolist()
            
            top_months = sorted_months[:2]
            top_month_names = [months_map[m] for m in top_months]
            best_avg_price = monthly_means[top_months[0]]
            curr_symbol = self.product.currency
            empirical_note = f"Based on 10-year historical data for '{self.product.title}', {top_month_names[0]} consistently records the lowest average price ({curr_symbol}{best_avg_price:,.2f}), followed by {top_month_names[1]}."

        # Domain category / product specific seasonal advice rules
        title_lower = self.product.title.lower()

        if any(k in title_lower for k in ["iphone", "macbook", "ipad", "apple", "pixel", "galaxy", "samsung", "oneplus", "smartphone", "phone"]):
            cat_advice = "For smartphones & Apple/flagship tech, the prime buying window is September–October (when previous generations drop following new flagship releases) and November (Black Friday & Festive Sales)."
        elif any(k in title_lower for k in ["laptop", "pc", "dell", "hp", "lenovo", "asus", "rtx", "gpu"]):
            cat_advice = "For laptops & computers, the best discount windows are August–September (Back-to-School sales) and November (Black Friday / Cyber Monday)."
        elif any(k in title_lower for k in ["ps5", "playstation", "xbox", "nintendo", "console", "game", "switch"]):
            cat_advice = "For gaming consoles & electronics, key discount windows occur during Mid-Year Summer Sales (June–July) and Holiday Black Friday (November–December)."
        elif any(k in title_lower for k in ["shoe", "nike", "adidas", "puma", "sneaker", "apparel", "clothing", "wear"]):
            cat_advice = "For footwear & apparel, top discounts happen during End-of-Season Clearances in January–February (Winter clearance) and July–August (Summer clearance)."
        elif any(k in title_lower for k in ["headphone", "earbud", "sony", "airpods", "bose", "audio", "speaker"]):
            cat_advice = "For headphones & audio gear, major price drops occur during Mid-Year Tech Promos (July) and Festive / Black Friday sales (November)."
        elif any(k in title_lower for k in ["tv", "television", "fridge", "washing", "appliance"]):
            cat_advice = "For TVs & major home appliances, optimal purchase windows are Festive/Diwali Sales (October–November) and New Model Clearance (January–February)."
        else:
            cat_advice = "For general merchandise, optimal buying windows coincide with Mid-Year Promotional Sales (July) and Year-End Festive Deals (November–December)."

        if empirical_note:
            return f"{cat_advice} {empirical_note}"
        else:
            return cat_advice

    def get_buying_recommendation(self) -> Dict[str, Any]:
        """
        Generates continuous, graph-position based deal scores and buying recommendations.
        Calculates exact position within 1-year and 10-year price boundaries.
        """
        stats = self.get_summary_statistics()
        current = stats["current_price"]
        atl = stats["all_time_low"]
        ath = stats["all_time_high"]
        mean_1y = stats["mean_1y_price"]
        min_1y = stats["min_1y_price"]
        max_1y = stats["max_1y_price"]
        avg_1y_diff_pct = stats["avg_1y_diff_pct"]
        target = self.product.target_price
        curr_symbol = stats["currency"]

        # 1. Position within 1-Year Range (0.0 = at 1y min, 1.0 = at 1y max)
        range_1y = max_1y - min_1y
        if range_1y > 0:
            pos_1y = (current - min_1y) / range_1y
        else:
            pos_1y = 0.5
        score_1y = 100.0 * (1.0 - pos_1y)

        # 2. Position within 10-Year Range (0.0 = at ATL, 1.0 = at ATH)
        range_10y = ath - atl
        if range_10y > 0:
            pos_10y = (current - atl) / range_10y
        else:
            pos_10y = 0.5
        score_10y = 100.0 * (1.0 - pos_10y)

        # 3. Deviation from 1-Year Average
        mean_dev_score = max(0.0, min(100.0, 50.0 - (avg_1y_diff_pct * 2.5)))

        # Weighted raw score calculation (0 to 100 continuous scale)
        raw_score = (0.50 * score_1y) + (0.25 * score_10y) + (0.25 * mean_dev_score)

        # Bonuses / Penalties
        reasoning = []
        key_insights = []

        # Target price check
        if target:
            if current <= target:
                raw_score += 15.0
                reasoning.append(f"Current price ({curr_symbol} {current:,.2f}) is below your target price of {curr_symbol} {target:,.2f}.")
            else:
                diff_targ = ((current - target) / target) * 100.0
                reasoning.append(f"Target price ({curr_symbol} {target:,.2f}) is {diff_targ:.1f}% below current price.")

        # Recent price drop check
        drops = self.detect_price_drops()
        recent_drop = drops[-1] if drops else None
        if recent_drop and recent_drop["date"] == stats.get("latest_date", ""):
            raw_score += 10.0
            reasoning.append(f"Active sale event: Price dropped by {curr_symbol} {recent_drop['drop_amount']:,.2f} (-{recent_drop['drop_percent']:.1f}%) on {recent_drop['date']}.")

        final_score = int(round(min(100.0, max(0.0, raw_score))))

        # Determine precise rating category & tier text based on final score & graph position
        if final_score >= 80:
            rating = "GREAT DEAL (BUY NOW)"
            key_insights.append("Price is sitting near the bottom of the annual price graph range.")
        elif final_score >= 65:
            rating = "STRONG BUY"
            key_insights.append("Favorable discount relative to annual moving average.")
        elif final_score >= 50:
            rating = "GOOD DEAL"
            key_insights.append("Moderately discounted retail price.")
        elif final_score >= 38:
            rating = "FAIR RETAIL PRICE"
            key_insights.append("Standard retail price without major active promotion.")
        elif final_score >= 22:
            rating = "HIGH PRICE - WAIT FOR DISCOUNT"
            key_insights.append("Price is near the upper bound of the recent 1-year graph range.")
        else:
            rating = "OVERPRICED - PEAK ATH PRICE"
            key_insights.append("Peak pricing phase — recommend waiting for upcoming seasonal clearance.")

        # Detailed graph position reasoning
        reasoning.append(f"Current price ({curr_symbol} {current:,.2f}) sits at {int((1.0 - pos_1y) * 100)}% discount percentile within 1-Year range ({curr_symbol} {min_1y:,.2f} – {curr_symbol} {max_1y:,.2f}).")
        
        if avg_1y_diff_pct < 0:
            reasoning.append(f"Current price is {abs(avg_1y_diff_pct):.1f}% below 1-Year Average ({curr_symbol} {mean_1y:,.2f}).")
        else:
            reasoning.append(f"Current price is {avg_1y_diff_pct:+.1f}% above 1-Year Average ({curr_symbol} {mean_1y:,.2f}).")

        # Dynamic product-specific seasonal advice
        seasonal_advice = self._calculate_best_buying_months()

        return {
            "rating": rating,
            "score": final_score,
            "current_price": current,
            "currency": stats["currency"],
            "target_price": target,
            "reasoning": reasoning,
            "key_insights": key_insights,
            "seasonal_advice": seasonal_advice,
            "summary_stats": stats
        }

