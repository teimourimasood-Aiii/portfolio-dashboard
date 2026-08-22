import requests
import json
import re
from bs4 import BeautifulSoup

# ---------- دریافت قیمت طلا و دلار از tgju.org ----------
def get_gold_and_dollar():
    try:
        url = "https://www.tgju.org/"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            
            # قیمت دلار
            dollar_elem = soup.find("span", {"data-field": "price_dollar_rl"})
            dollar = dollar_elem.text.replace(",", "").strip() if dollar_elem else None
            
            # قیمت طلای ۱۸ عیار
            gold_elem = soup.find("span", {"data-field": "price_gold_18"})
            gold = gold_elem.text.replace(",", "").strip() if gold_elem else None
            
            return float(dollar) if dollar else None, float(gold) if gold else None
    except Exception as e:
        print(f"خطا در دریافت از tgju: {e}")
    return None, None

# ---------- دریافت قیمت سهام از tsetmc.com ----------
def get_stock_price(symbol):
    try:
        # برای هر سهم، باید کد شناسایی (InsCode) را پیدا کنیم
        # فعلاً از یک روش ساده استفاده می‌کنیم
        url = f"https://www.tsetmc.com/Loader.aspx?ParTree=151311&i={symbol}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            # داده‌ها به صورت JSON هستند
            data = r.json()
            price = data.get("pDrCotVal")  # قیمت لحظه‌ای
            if price and float(price) > 0:
                return float(price)
        return 0
    except:
        return 0

# ========== اجرای اصلی ==========
print("🔄 در حال دریافت قیمت‌ها از tgju.org...")

# دریافت طلا و دلار
dollar, gold = get_gold_and_dollar()
print(f"دلار: {dollar}")
print(f"طلا ۱۸: {gold}")

# دریافت قیمت سهام (با کدهای شناسایی)
# توجه: برای هر سهم باید InsCode را پیدا کنید
stock_prices = {
    "اخابر": get_stock_price("46348559193224090"),  # InsCode اخابر
    "اهرم": get_stock_price("65889254712345678"),   # InsCode اهرم (نمونه)
    "فارماکیان": get_stock_price("98765432109876543") # InsCode فارماکیان (نمونه)
}
print(f"قیمت سهام: {stock_prices}")

# ذخیره در فایل prices.json
prices = {
    "دلار": dollar if dollar else 0,
    "طلا_۱۸": gold if gold else 0,
    **stock_prices
}

with open("prices.json", "w", encoding="utf-8") as f:
    json.dump(prices, f, ensure_ascii=False, indent=2)

print("✅ قیمت‌ها با موفقیت به‌روز شدند!")
