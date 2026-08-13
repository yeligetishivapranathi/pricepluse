import unittest
from pricepulse.google_api import GooglePriceFetcher
from pricepulse.analyzer import PriceAnalyzer

class TestGoogleAPIAndAnalyzer(unittest.TestCase):

    def test_search_and_build_product(self):
        fetcher = GooglePriceFetcher()
        product = fetcher.search_and_build_product("iPhone 15 Pro")

        self.assertIsNotNone(product.title)
        self.assertTrue(len(product.price_history) >= 100) # 10 years of monthly data
        self.assertGreater(product.current_price, 0)

    def test_analyzer_statistics(self):
        fetcher = GooglePriceFetcher()
        product = fetcher.search_and_build_product("PlayStation 5")

        analyzer = PriceAnalyzer(product)
        stats = analyzer.get_summary_statistics()
        rec = analyzer.get_buying_recommendation()

        self.assertEqual(stats["title"], product.title)
        self.assertIn("all_time_low", stats)
        self.assertIn("mean_10y_price", stats)
        self.assertIsNotNone(rec["rating"])
        self.assertTrue(0 <= rec["score"] <= 100)

    def test_dynamic_best_time_to_buy(self):
        fetcher = GooglePriceFetcher()
        
        iphone = fetcher.search_and_build_product("iPhone 15 Pro")
        shoes = fetcher.search_and_build_product("Nike Air Max Shoes")
        audio = fetcher.search_and_build_product("Sony WH-1000XM5 Headphones")

        iphone_rec = PriceAnalyzer(iphone).get_buying_recommendation()
        shoes_rec = PriceAnalyzer(shoes).get_buying_recommendation()
        audio_rec = PriceAnalyzer(audio).get_buying_recommendation()

        # Ensure dynamic seasonal advice is non-empty and tailored
        self.assertIn("smartphones", iphone_rec["seasonal_advice"].lower())
        self.assertIn("footwear", shoes_rec["seasonal_advice"].lower())
        self.assertIn("headphones", audio_rec["seasonal_advice"].lower())

        # Ensure seasonal advice differs across categories
        self.assertNotEqual(iphone_rec["seasonal_advice"], shoes_rec["seasonal_advice"])

if __name__ == "__main__":
    unittest.main()
