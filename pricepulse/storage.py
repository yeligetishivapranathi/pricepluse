"""
JSON Storage & File Handling for PricePulse.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
#import pandas as pd

from pricepulse.models import Product
from pricepulse.logger import setup_logger
from pricepulse.exceptions import ProductNotFoundError, PricePulseException

logger = setup_logger("Storage")

class StorageManager:
    """Manages reading, writing, and querying JSON product database files."""

    def __init__(self, data_file: str = "data/products.json"):
        self.data_file = Path(data_file)
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.data_file.exists():
            self._write_raw({})

    def _read_raw(self) -> Dict[str, dict]:
        """Reads raw JSON content from disk."""
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Data file read error or missing ({e}). Initializing empty database.")
            return {}

    def _write_raw(self, data: Dict[str, dict]):
        """Writes raw dict to JSON disk file safely."""
        try:
            temp_file = self.data_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            temp_file.replace(self.data_file)
        except Exception as e:
            logger.error(f"Failed writing to data file {self.data_file}: {e}")
            raise PricePulseException(f"Database write failure: {e}")

    def save_product(self, product: Product) -> Product:
        """Saves or updates a Product instance in the JSON database."""
        db = self._read_raw()
        db[product.product_id] = product.to_dict()
        self._write_raw(db)
        logger.info(f"Product '{product.title}' (ID: {product.product_id}) saved successfully.")
        return product

    def get_product(self, product_id: str) -> Product:
        """Retrieves a Product instance by product_id."""
        clean_id = Product.clean_product_id(product_id)
        db = self._read_raw()
        if clean_id not in db:
            raise ProductNotFoundError(f"Product with ID '{product_id}' not found.")
        return Product.from_dict(db[clean_id])

    def find_product_by_query(self, query: str) -> Optional[Product]:
        """Searches for a product by ID or title matching query."""
        clean_query = query.strip().lower()
        db = self._read_raw()
        
        # 1. Exact ID match
        clean_id = Product.clean_product_id(query)
        if clean_id in db:
            return Product.from_dict(db[clean_id])

        # 2. Search in title or brand
        for p_id, p_data in db.items():
            title = p_data.get("title", "").lower()
            if clean_query in title or clean_query in p_id:
                return Product.from_dict(p_data)
                
        return None

    def list_products(self) -> List[Product]:
        """Lists all saved products in database."""
        db = self._read_raw()
        return [Product.from_dict(data) for data in db.values()]

    def delete_product(self, product_id: str) -> bool:
        """Deletes a product by product_id."""
        clean_id = Product.clean_product_id(product_id)
        db = self._read_raw()
        if clean_id in db:
            del db[clean_id]
            self._write_raw(db)
            logger.info(f"Deleted product ID '{clean_id}'")
            return True
        return False

    def export_to_csv(self, product_id: str, output_path: str) -> str:
        """Exports a product's historical price data to CSV using Pandas."""
        product = self.get_product(product_id)
        if not product.price_history:
            raise PricePulseException(f"No price history available for '{product.title}'.")
        
        df = pd.DataFrame([pt.to_dict() for pt in product.price_history])
        df["product_id"] = product.product_id
        df["product_title"] = product.title
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Exported price history for {product.title} to {output_path}")
        return output_path
