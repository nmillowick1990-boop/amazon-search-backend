import os
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"

AMAZON_ACCESS_KEY = os.getenv("AMAZON_ACCESS_KEY", "")
AMAZON_SECRET_KEY = os.getenv("AMAZON_SECRET_KEY", "")
AMAZON_ASSOCIATE_TAG = os.getenv("AMAZON_ASSOCIATE_TAG", "")
AMAZON_COUNTRY = os.getenv("AMAZON_COUNTRY", "AU")

MAX_RESULTS = 8

MOCK_RESULTS = [
    {"title": "Example Wireless Mouse - Ergonomic, USB-C", "price": "$24.99", "asin": "B000MOCK01"},
    {"title": "Example Wireless Mouse Pro - Silent Click, RGB", "price": "$34.50", "asin": "B000MOCK02"},
    {"title": "Example Compact Mouse - Bluetooth, Lightweight", "price": "$19.00", "asin": "B000MOCK03"},
    {"title": "Example Gaming Mouse - 16000 DPI, Programmable", "price": "$49.99", "asin": "B000MOCK04"},
]


def build_keywords(main_item, feature1, feature2, feature3):
    parts = [p.strip() for p in [main_item, feature1, feature2, feature3] if p and p.strip()]
    return " ".join(parts)


def search_amazon_live(keywords):
    # Requires the 'python-amazon-paapi' package and an APPROVED PA-API account
    # (Amazon activates API access only after 3 qualifying Associate sales).
    from amazon_paapi import AmazonApi
    from amazon_paapi.models import Country

    country_map = {
        "AU": Country.AU,
        "US": Country.US,
        "UK": Country.UK,
        "CA": Country.CA,
    }
    country = country_map.get(AMAZON_COUNTRY.upper(), Country.AU)

    amazon = AmazonApi(AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, AMAZON_ASSOCIATE_TAG, country)
    search_result = amazon.search_items(keywords=keywords, item_count=MAX_RESULTS)

    results = []
    for item in getattr(search_result, "items", [])[:MAX_RESULTS]:
        title = getattr(item.item_info.title, "display_value", "Unknown item") if item.item_info and item.item_info.title else "Unknown item"
        price = "N/A"
        if item.offers and item.offers.listings:
            price = item.offers.listings[0].price.display_amount
        asin = item.asin or ""
        results.append({"title": title[:100], "price": price, "asin": asin})
    return results


@app.route("/search", methods=["POST"])
def search():
    data = request.get_json(silent=True) or {}
    main_item = data.get("main_item", "")
    feature1 = data.get("feature1", "")
    feature2 = data.get("feature2", "")
    feature3 = data.get("feature3", "")

    if not main_item.strip():
        return jsonify({"error": "main_item is required"}), 400

    keywords = build_keywords(main_item, feature1, feature2, feature3)
    app.logger.info("Search request: %s", keywords)

    try:
        if MOCK_MODE:
            results = MOCK_RESULTS
        else:
            results = search_amazon_live(keywords)
        return jsonify({"results": results})
    except Exception as e:
        app.logger.exception("Search failed")
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "mock_mode": MOCK_MODE})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
