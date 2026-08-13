import unittest
from pricepulse.models import Product, PricePoint, parse_price_string
from pricepulse.exceptions import InvalidPriceDataError

class TestModels(unittest.TestCase):

    def test_parse_price_string(self):
        self.assertEqual(parse_price_string("$1,299.99"), 1299.99)
        self.assertEqual(parse_price_string("Rs. 45,000"), 45000.0)
        self.assertEqual(parse_price_string("EUR 250.50"), 250.50)
        self.assertEqual(parse_price_string(99.9), 99.9)

        with self.assertRaises(InvalidPriceDataError):
            parse_price_string("No Numbers Here")

    def test_product_creation_and_clean_id(self):
        prod = Product(
            product_id="Sony WH-1000XM5 Headphones!",
            title="Sony WH-1000XM5 Wireless Headphones",
            current_price="$399.99",
            currency="USD"
        )
        self.assertEqual(prod.product_id, "sony_wh-1000xm5_headphones")
        self.assertEqual(prod.current_price, 399.99)

    def test_add_price_point(self):
        prod = Product(product_id="test_prod", title="Test Product", current_price=100.0)
        prod.add_price_point("2026-01-01", 120.0)
        prod.add_price_point("2026-02-01", 95.0)
        self.assertEqual(len(prod.price_history), 2)
        self.assertEqual(prod.current_price, 95.0)

if __name__ == "__main__":
    unittest.main()
