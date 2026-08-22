import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
import os
from datetime import datetime

st.set_page_config(page_title="سبد پویا", layout="centered")
st.title("📊 سبد مادر (خودکار + دستی + سود/زیان)")

DATA_FILE = "portfolio_data.json"
PRICES_FILE = "prices.json"

# ---------- دریافت خودکار قیمت‌ها (با خطاگیری بهتر) ----------
def get_navasan_price(item):
    try:
        url = f"https://api.navasan.tech/latest/?api_key=free&item={item}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if item in data:
                return float(data[item]["value"].replace(",", ""))
        return None
    except:
        return None

def get_bitcoin_price(dollar_price):
    try:
        if dollar_price is None:
            return None
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        r = requests.get(url, timeout=5)
        data = r.json()
        return float(data["bitcoin"]["usd"]) * dollar_price
    except:
        return None

# ---------- بارگذاری و ذخیره قیمت‌ها ----------
def load_prices():
    default_prices = {
        "دلار": 190000,
        "طلا ۱۸": 19800000,
        "بیت‌کوین": 4200000000,
        "نقد": 1
    }
    if os.path.exists(PRICES_FILE):
        with open(PRICES_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
            # ترکیب قیمت‌های ذخیره‌شده با پیش‌فرض (برای مواردی که در فایل نیستند)
            for key, value in default_prices.items():
                if key not in saved:
                    saved[key] = value
            return saved
    return default_prices

def save_prices(prices):
    with open(PRICES_FILE, "w", encoding="utf-8") as f:
        json.dump(prices, f, ensure_ascii=False, indent=2)

# ---------- بارگذاری و ذخیره داده سبد ----------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {
            "assets": [
                {"name": "اخابر", "count": 285000, "unit": "سهم", "buy_price": 0},
                {"name": "اهرم", "count": 3000, "unit": "سهم", "buy_price": 0},
                {"name": "فارماکیان", "count": 1500, "unit": "سهم", "buy_price": 0},
                {"name": "طلا ۱۸", "count": 45, "unit": "گرم", "buy_price": 0},
                {"name": "دلار", "count": 1800, "unit": "دلار", "buy_price": 0},
                {"name": "بیت‌کوین", "count": 0.007025, "unit": "BTC", "buy_price": 0},
                {"name": "نقد", "count": 500000000, "unit": "تومان", "buy_price": 1}
            ]
        }

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ========== بارگذاری ==========
data = load_data()
assets = data["assets"]
prices = load_prices()

# ---------- دریافت قیمت‌های خودکار (با نگهداری قیمت قبلی در صورت خطا) ----------
auto_dollar = get_navasan_price("usd")
if auto_dollar is not None:
    prices["دلار"] = auto_dollar

auto_gold = get_navasan_price("18ayar")
if auto_gold is not None:
    prices["طلا ۱۸"] = auto_gold

auto_btc = get_bitcoin_price(auto_dollar if auto_dollar else prices.get("دلار", 190000))
if auto_btc is not None:
    prices["بیت‌کوین"] = auto_btc

# ========== منوی کناری ==========
with st.sidebar:
    st.header("⚙️ مدیریت سبد")
    
    # ---------- بخش ورود قیمت روزانه ----------
    st.subheader("📝 ورود قیمت‌های روزانه")
    st.caption("قیمت سهام را خودتان وارد کنید. قیمت طلا/دلار/بیت‌کوین خودکار است.")
    
    new_prices = {}
    for asset in assets:
        name = asset["name"]
        current = prices.get(name, 0)
        
        # نمایش وضعیت دریافت خودکار
        if name == "دلار":
            st.info(f"🟢 دلار: {prices.get('دلار', 0):,.0f} تومان (خودکار)")
            new_prices[name] = prices.get('دلار', 0)
        elif name == "طلا ۱۸":
            st.info(f"🟢 طلا ۱۸: {prices.get('طلا ۱۸', 0):,.0f} تومان (خودکار)")
            new_prices[name] = prices.get('طلا ۱۸', 0)
        elif name == "بیت‌کوین":
            st.info(f"🟢 بیت‌کوین: {prices.get('بیت‌کوین', 0):,.0f} تومان (خودکار)")
            new_prices[name] = prices.get('بیت‌کوین', 0)
        elif name == "نقد":
            new_prices[name] = 1  # نقد همیشه ۱ است
            st.info("🟣 نقد: ۱ تومان (ثابت)")
        else:
            new_price = st.number_input(
                f"{name} (هر {asset['unit']})",
                min_value=0,
                value=current,
                step=100,
                key=f"price_{name}"
            )
            new_prices[name] = new_price
    
    if st.button("💾 ذخیره قیمت‌های دستی"):
        save_prices(new_prices)
        st.success("✅ قیمت‌ها ذخیره شدند!")
        st.rerun()
    
    st.divider()
    
    # ---------- ویرایش تعداد و قیمت خرید ----------
    st.subheader("✏️ ویرایش دارایی")
    if len(assets) > 0:
        selected_name = st.selectbox("انتخاب دارایی", [a["name"] for a in assets])
        selected = next(a for a in assets if a["name"] == selected_name)
        
        new_count = st.number_input("تعداد جدید", min_value=0.0, step=0.01, value=float(selected["count"]))
        new_buy = st.number_input("قیمت میانگین خرید (تومان)", min_value=0, value=int(selected["buy_price"]))
        
        if st.button("💾 ذخیره تغییرات"):
            for a in assets:
                if a["name"] == selected_name:
                    a["count"] = new_count
                    a["buy_price"] = new_buy
                    break
            save_data(data)
            st.success("✅ به‌روز شد!")
            st.rerun()
    
    st.divider()
    
    # ---------- اضافه کردن دارایی جدید ----------
    st.subheader("➕ اضافه کردن دارایی جدید")
    new_name = st.text_input("نام دارایی")
    new_count = st.number_input("تعداد", min_value=0.0, step=0.01, value=1.0)
    new_unit = st.text_input("واحد")
    new_buy = st.number_input("قیمت خرید (تومان)", min_value=0, value=0)
    
    if st.button("➕ اضافه کن", key="add_btn"):
        if new_name and new_count > 0:
            assets.append({
                "name": new_name,
                "count": new_count,
                "unit": new_unit if new_unit else "-",
                "buy_price": new_buy
            })
            save_data(data)
            st.success(f"✅ {new_name} اضافه شد!")
            st.rerun()
    
    st.divider()
    
    # ---------- حذف دارایی ----------
    st.subheader("🗑️ حذف دارایی")
    if len(assets) > 0:
        delete_name = st.selectbox("انتخاب دارایی برای حذف", [a["name"] for a in assets])
        if st.button("🗑️ حذف کن", key="delete_btn"):
            assets = [a for a in assets if a["name"] != delete_name]
            data["assets"] = assets
            save_data(data)
            st.success(f"✅ {delete_name} حذف شد!")
            st.rerun()

# ========== محاسبه ارزش سبد و سود/زیان ==========
df = pd.DataFrame(assets)
df["قیمت_لحظه‌ای"] = df["name"].apply(lambda x: prices.get(x, 0))
df["ارزش_تومان"] = df["count"] * df["قیمت_لحظه‌ای"]
df["ارزش_خرید"] = df["count"] * df["buy_price"]
df["سود_زیان_تومان"] = df["ارزش_تومان"] - df["ارزش_خرید"]
df["درصد_سود"] = df.apply(
    lambda row: (row["سود_زیان_تومان"] / row["ارزش_خرید"] * 100) if row["ارزش_خرید"] > 0 else 0,
    axis=1
)

total_value = df["ارزش_تومان"].sum()
total_buy = df["ارزش_خرید"].sum()
total_profit = total_value - total_buy
total_profit_percent = (total_profit / total_buy * 100) if total_buy > 0 else 0

# ========== نمایش داشبورد ==========
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("💰 ارزش کل سبد", f"{total_value:,.0f} تومان")
with col2:
    st.metric("📈 سود/زیان کل", f"{total_profit:+,.0f} تومان", delta=f"{total_profit_percent:+.2f}%")
with col3:
    st.metric("🕒 بروزرسانی", datetime.now().strftime('%H:%M'))

st.subheader("📋 لیست دارایی‌ها")
display_df = df[["name", "count", "قیمت_لحظه‌ای", "unit", "ارزش_تومان", "buy_price", "سود_زیان_تومان", "درصد_سود"]]
display_df.columns = ["دارایی", "تعداد", "قیمت (تومان)", "واحد", "ارزش (تومان)", "قیمت خرید", "سود/زیان", "درصد"]

st.dataframe(
    display_df,
    column_config={
        "قیمت (تومان)": st.column_config.NumberColumn(format="%.0f"),
        "ارزش (تومان)": st.column_config.NumberColumn(format="%.0f"),
        "قیمت خرید": st.column_config.NumberColumn(format="%.0f"),
        "سود/زیان": st.column_config.NumberColumn(format="%.0f"),
        "درصد": st.column_config.NumberColumn(format="%.2f%%")
    },
    use_container_width=True,
    height=350
)

st.subheader("🎯 ترکیب سبد")
df_chart = df[df["ارزش_تومان"] > 0].copy()
if len(df_chart) > 0:
    fig = px.pie(df_chart, values="ارزش_تومان", names="name", hole=0.4)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("هیچ دارایی با ارزش مثبت وجود ندارد.")

st.caption("💡 قیمت طلا، دلار و بیت‌کوین خودکار دریافت می‌شوند. قیمت سهام را روزانه در منوی کناری وارد کنید.")
