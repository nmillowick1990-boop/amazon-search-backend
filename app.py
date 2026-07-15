import os
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"

SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
AMAZON_DOMAIN = os.getenv("AMAZON_DOMAIN", "amazon.com.au")

MAX_RESULTS = 6  # kept small - each result includes an image the ESP32 has to download+decode

MOCK_RESULTS = [
    {
        "title": "Example Wireless Mouse - Ergonomic, USB-C",
        "price": "$24.99",
        "seller": "Amazon AU",
        "image": "https://http.cat/images/200.jpg",
    },
    {
        "title": "Example Wireless Mouse Pro - Silent Click, RGB",
        "price": "$34.50",
        "seller": "TechGear Store",
        "image": "https://http.cat/images/201.jpg",
    },
    {
        "title": "Example Compact Mouse - Bluetooth, Lightweight",
        "price": "$19.00",
        "seller": "Amazon AU",
        "image": "https://http.cat/images/202.jpg",
    },
]


def build_keywords(main_item, feature1, feature2, feature3):
    parts = [p.strip() for p in [main_item, feature1, feature2, feature3] if p and p.strip()]
    return " ".join(parts)


def extract_price(item):
    price = item.get("price")
    if isinstance(price, dict):
        return price.get("raw") or (f"${price.get('value')}" if price.get("value") else "N/A")
    if isinstance(price, str) and price:
        return price
    return "N/A"


def extract_seller(item):
    seller = item.get("seller")
    if isinstance(seller, dict):
        return seller.get("name") or "Amazon"
    if isinstance(seller, str) and seller:
        return seller
    return "Amazon"


def extract_image(item):
    return item.get("thumbnail") or ""


def search_amazon_live(keywords):
    from serpapi import GoogleSearch

    params = {
        "engine": "amazon",
        "k": keywords,
        "amazon_domain": AMAZON_DOMAIN,
        "api_key": SERPAPI_KEY,
    }
    search = GoogleSearch(params)
    data = search.get_dict()

    if "error" in data:
        raise RuntimeError(data["error"])

    organic = data.get("organic_results", [])
    results = []
    for item in organic[:MAX_RESULTS]:
        results.append({
            "title": (item.get("title") or "Unknown item")[:100],
            "price": extract_price(item),
            "seller": extract_seller(item),
            "image": extract_image(item),
        })
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
