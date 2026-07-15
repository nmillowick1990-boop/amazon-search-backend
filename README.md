# Amazon Search Backend

A tiny Flask API that the ESP32 calls to search Amazon Australia via
**SerpApi** (no Amazon Associates account or sales history required).
Ships in **mock mode** by default so you can test the whole system before
you have a SerpApi key.

## Endpoint

`POST /search`

Request body:
```json
{
  "main_item": "wireless mouse",
  "feature1": "bluetooth",
  "feature2": "under $30",
  "feature3": "black"
}
```

Response:
```json
{
  "results": [
    {"title": "...", "price": "$24.99", "seller": "Amazon AU", "image": "https://..."},
    ...
  ]
}
```

## Local testing

```bash
cd amazon-search-backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # leave MOCK_MODE=true for now
python app.py
```

Test it:
```bash
curl -X POST http://localhost:5000/search \
  -H "Content-Type: application/json" \
  -d '{"main_item":"wireless mouse","feature1":"bluetooth","feature2":"","feature3":""}'
```

## Deploying to the cloud (Render.com, free tier)

1. Push this `amazon-search-backend` folder to a GitHub repo.
2. On [render.com](https://render.com): **New -> Web Service**, point it at
   the repo.
3. Settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
4. Under **Environment**, add the variables from `.env.example`
   (`MOCK_MODE=true` to start, plus your SerpApi key once you have one).
5. Deploy. Render gives you a URL like `https://your-app.onrender.com` —
   that's the `BACKEND_URL` the ESP32 needs (see the firmware's `Config.h`).

Note: Render's free tier spins down after inactivity and takes ~30-50
seconds to wake up on the next request — the firmware's HTTP timeout is
generous to account for this.

## Getting a SerpApi key (no sales/approval needed)

1. Sign up at [serpapi.com](https://serpapi.com/) — free plan includes
   100 searches/month, no waiting period or sales requirement.
2. Copy your API key from the dashboard into `SERPAPI_KEY`.
3. Set `MOCK_MODE=false` and redeploy.
4. Paid plans exist if you need more than 100 searches/month.

## Known limitation: seller field

Amazon's search-results page (which SerpApi reads) doesn't always expose
the specific third-party marketplace seller — that detail usually only
appears on the full product page. When it's not available, this backend
falls back to showing `"Amazon"` as the seller rather than leaving it
blank. If you need the real "Sold by" value reliably, that would require
an extra product-detail lookup per result (more API calls = higher cost),
which isn't implemented here to keep things simple and fast.

## Notes

- Results capped at 6 items per search (fewer than before, since each one
  now carries an image the ESP32 has to download and decode).
- Title text truncated to 100 characters.
