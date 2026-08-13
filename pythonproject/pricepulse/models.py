"""
OOP Data Models for PricePulse.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
import re
from typing import List, Optional, Dict, Any
from pricepulse.exceptions import InvalidPriceDataError

def parse_price_string(price_str: Any) -> float:
    """
    Uses Regular Expressions (Regex) to extract clean float price from strings
    like '$1,299.99', 'Rs. 45,000', 'EUR 250.50', etc.
    """
    if isinstance(price_str, (int, float)):
        return float(price_str)
    
    if not price_str or not isinstance(price_str, str):
        raise InvalidPriceDataError(f"Invalid price value: {price_str}")

    # Use Regex to match digits, commas, and dots
    # Removes currency symbols and comma separators
    cleaned = re.sub(r'[^\d.]', '', price_str.replace(',', ''))
    
    # Handle multiple decimals if present by keeping first valid float pattern
    match = re.search(r'\d+(\.\d{1,2})?', cleaned)
    if not match:
        raise InvalidPriceDataError(f"Could not extract numeric price from '{price_str}'")

    try:
        return float(match.group(0))
    except ValueError:
        raise InvalidPriceDataError(f"Failed to convert '{price_str}' to float price.")


@dataclass
class PricePoint:
    """Represents a single historical price recording."""
    date: str  # YYYY-MM-DD format
    price: float
    platform: str = "Google Shopping"
    in_stock: bool = True
    notes: str = ""

    def __post_init__(self):
        # Validate date format or convert
        if isinstance(self.price, str):
            self.price = parse_price_string(self.price)
        elif not isinstance(self.price, (int, float)) or self.price < 0:
            raise InvalidPriceDataError(f"Price must be a non-negative number, got: {self.price}")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PricePoint":
        return cls(**data)


class Product:
    """OOP Model for a tracked product."""
    def __init__(
        self,
        product_id: str,
        title: str,
        category: str = "General",
        brand: str = "Generic",
        current_price: float = 0.0,
        currency: str = "₹",
        target_price: Optional[float] = None,
        url: str = "",
        price_history: Optional[List[PricePoint]] = None
    ):
        self.product_id = self.clean_product_id(product_id)
        self.title = title.strip()
        self.category = category.strip()
        self.brand = brand.strip()
        self.currency = currency.strip().upper()
        self.url = url.strip()
        self.target_price = target_price
        
        self.price_history: List[PricePoint] = price_history if price_history is not None else []
        self._current_price = parse_price_string(current_price) if current_price else 0.0

        if self.price_history and not self._current_price:
            self._current_price = self.price_history[-1].price

    @staticmethod
    def clean_product_id(product_id: str) -> str:
        """Regex helper to create safe, clean ID from title or input."""
        cleaned = re.sub(r'[^a-zA-Z0-9_-]', '_', product_id.strip().lower())
        cleaned = re.sub(r'_+', '_', cleaned).strip('_')
        return cleaned or "product_unknown"

    @property
    def current_price(self) -> float:
        if self.price_history:
            return self.price_history[-1].price
        return self._current_price

    @current_price.setter
    def current_price(self, val: float):
        self._current_price = parse_price_string(val)

    def add_price_point(self, date_str: str, price: float, platform: str = "Google Shopping", in_stock: bool = True, notes: str = ""):
        """Appends a new price point and keeps history sorted by date."""
        pt = PricePoint(date=date_str, price=parse_price_string(price), platform=platform, in_stock=in_stock, notes=notes)
        self.price_history.append(pt)
        # Sort price history chronologically
        self.price_history.sort(key=lambda x: x.date)
        self._current_price = self.price_history[-1].price

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_id": self.product_id,
            "title": self.title,
            "category": self.category,
            "brand": self.brand,
            "current_price": self.current_price,
            "currency": self.currency,
            "target_price": self.target_price,
            "url": self.url,
            "price_history": [pt.to_dict() for pt in self.price_history]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Product":
        history = [PricePoint.from_dict(p) for p in data.get("price_history", [])]
        return cls(
            product_id=data["product_id"],
            title=data["title"],
            category=data.get("category", "General"),
            brand=data.get("brand", "Generic"),
            current_price=data.get("current_price", 0.0),
            currency=data.get("currency", "₹"),
            target_price=data.get("target_price"),
            url=data.get("url", ""),
            price_history=history
        )

    def __repr__(self) -> str:
        return f"<Product id='{self.product_id}' title='{self.title}' price={self.currency}{self.current_price}>"
