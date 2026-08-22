import requests
import json
import os

BRSAPI_KEY = os.environ.get('BRSAPI_KEY')
SYMBOLS = ["اخابر", "اهرم", "فارماکیان"]

def get_stock_price(symbol):
    try:
        url = f"https://api.brsapi.ir/Tsetmc/Price.php?key={BRSAPI_KEY}&symbol={symbol}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            price = data.get("price") or data.get("pDrCotVal")
            if price and float(price) > 0:
                return float(price)
        return 0
    except:
        return 0

prices = {}
for symbol in SYMBOLS:
    prices[symbol] = get_stock_price(symbol)

with open("prices.json", "w", encoding="utf-8") as f:
    json.dump(prices, f, ensure_ascii=False, indent=2)

print("✅ Prices updated")
