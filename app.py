import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
import os
from datetime import datetime

st.set_page_config(page_title="سبد پویا", layout="centered")
st.title("📊 سبد مادر (با قیمت‌های ذخیره‌شده)")

DATA_FILE = "portfolio_data.json"
PRICES_FILE = "prices.json"

# ---------- قیمت طلا و دلار از Navasan ----------
def get_navasan_price(item):
    try:
        url = f"https://api.navasan.tech/latest/?api_key=free&item={item}"
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            data = r.json()
            if item in data:
                value = data[item]["value"].replace(",", "")
                return float(value)
        return None
    except:
        return None

def get_dollar_price():
    return get_navasan_price("usd")

def get_gold18_price():
    return get_navasan_price("18ayar")

# ---------- قیمت بیت‌کوین از CoinGecko ----------
def get_bitcoin_price():
    try:
        dollar = get_dollar_price()
        if dollar is None:
            dollar = 190000
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        r = requests.get(url, timeout=8)
        data = r.json()
        btc_usd = float(data["bitcoin"]["usd"])
        return btc_usd * dollar
    except:
        return 4200000000

# ---------- خواندن قیمت سهام از فایل JSON ----------
def load_stock_prices():
    if os.path.exists(PRICES_FILE):
        with open(PRICES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def get_stock_price(symbol):
    prices = load_stock_prices()
    return prices.get(symbol, 0)

# ---------- تابع اصلی دریافت قیمت ----------
def get_price(asset):
    source = asset.get("source", "")
    if source == "Navasan - دلار":
        return get_dollar_price()
    elif source == "Navasan - طلا ۱۸":
        return get_gold18_price()
    elif source == "BrsAPI - سهام":
        return get_stock_price(asset.get("identifier", ""))
    elif source == "CoinGecko - بیت‌کوین":
        return get_bitcoin_price()
    elif source == "دستی":
        return asset.get("manual_price", 0)
    return 0

# ---------- بارگذاری و ذخیره داده سبد ----------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {
            "assets": [
                {"name": "اخابر", "count": 285000, "source": "BrsAPI - سهام", "identifier": "اخابر", "unit": "سهم", "manual_price": 0},
                {"name": "اهرم", "count": 3000, "source": "BrsAPI - سهام", "identifier": "اهرم", "unit": "سهم", "manual_price": 0},
                {"name": "فارماکیان", "count": 1500, "source": "BrsAPI - سهام", "identifier": "فارماکیان", "unit": "سهم", "manual_price": 0},
                {"name": "طلا ۱۸", "count": 45, "source": "Navasan - طلا ۱۸", "identifier": "", "unit": "گرم", "manual_price": 0},
                {"name": "دلار", "count": 1800, "source": "Navasan - دلار", "identifier": "", "unit": "دلار", "manual_price": 0},
                {"name": "بیت‌کوین", "count": 0.007025, "source": "CoinGecko - بیت‌کوین", "identifier": "", "unit": "BTC", "manual_price": 0},
                {"name": "نقد", "count": 500000000, "source": "دستی", "identifier": "", "unit": "تومان", "manual_price": 1}
            ]
        }

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ========== بارگذاری داده ==========
data = load_data()
assets = data["assets"]

# ========== منوی کناری ==========
with st.sidebar:
    st.header("⚙️ مدیریت کامل سبد")
    
    # اضافه کردن
    st.subheader("➕ اضافه کردن دارایی جدید")
    new_name = st.text_input("نام دارایی")
    new_count = st.number_input("تعداد/حجم", min_value=0.0, step=0.01, value=1.0)
    new_source = st.selectbox(
        "منبع قیمت",
        ["BrsAPI - سهام", "Navasan - دلار", "Navasan - طلا ۱۸", "CoinGecko - بیت‌کوین", "دستی"],
        key="add_source"
    )
    
    new_identifier = ""
    new_manual_price = 0
    if new_source == "BrsAPI - سهام":
        new_identifier = st.text_input("نماد (مثلاً اخابر)")
    elif new_source == "دستی":
        new_manual_price = st.number_input("قیمت دستی (تومان)", min_value=0.0, value=1.0)
    
    new_unit = st.text_input("واحد")
    
    if st.button("➕ اضافه کن", key="add_btn"):
        if new_name and new_count > 0:
            asset = {
                "name": new_name,
                "count": new_count,
                "source": new_source,
                "identifier": new_identifier,
                "unit": new_unit if new_unit else "-",
                "manual_price": new_manual_price
            }
            assets.append(asset)
            save_data(data)
            st.success(f"✅ {new_name} اضافه شد!")
            st.rerun()
        else:
            st.error("❌ نام و تعداد را وارد کنید.")
    
    st.divider()
    
    # ویرایش
    st.subheader("✏️ ویرایش دارایی موجود")
    if len(assets) > 0:
        asset_names = [a["name"] for a in assets]
        selected_name = st.selectbox("انتخاب دارایی برای ویرایش", asset_names, key="edit_select")
        
        selected_asset = None
        for a in assets:
            if a["name"] == selected_name:
                selected_asset = a
                break
        
        if selected_asset:
            st.caption(f"واحد: {selected_asset['unit']} | منبع: {selected_asset['source']}")
            
            new_count_edit = st.number_input(
                "تعداد جدید",
                min_value=0.0,
                step=0.01,
                value=float(selected_asset["count"]),
                key="edit_count"
            )
            
            if selected_asset["source"] == "دستی":
                new_manual_edit = st.number_input(
                    "قیمت دستی جدید (تومان)",
                    min_value=0.0,
                    value=float(selected_asset.get("manual_price", 0)),
                    key="edit_manual"
                )
            else:
                new_manual_edit = 0
            
            if st.button("💾 ذخیره تغییرات این دارایی", key="edit_btn"):
                for a in assets:
                    if a["name"] == selected_name:
                        a["count"] = new_count_edit
                        if a["source"] == "دستی":
                            a["manual_price"] = new_manual_edit
                        break
                save_data(data)
                st.success(f"✅ {selected_name} به‌روزرسانی شد!")
                st.rerun()
    else:
        st.info("هیچ دارایی برای ویرایش وجود ندارد.")
    
    st.divider()
    
    # حذف
    st.subheader("🗑️ حذف دارایی")
    if len(assets) > 0:
        delete_name = st.selectbox("انتخاب دارایی برای حذف", [a["name"] for a in assets], key="delete_select")
        if st.button("🗑️ حذف کن", key="delete_btn"):
            assets = [a for a in assets if a["name"] != delete_name]
            data["assets"] = assets
            save_data(data)
            st.success(f"✅ {delete_name} حذف شد!")
            st.rerun()
    else:
        st.info("هیچ دارایی برای حذف وجود ندارد.")

# ========== محاسبه قیمت‌ها و ارزش سبد ==========
prices = []
statuses = []

for a in assets:
    price = get_price(a)
    if price is None or price == 0:
        price = 0
        if a["source"] == "BrsAPI - سهام":
            statuses.append("🟡 قیمت در فایل JSON موجود نیست")
        else:
            statuses.append("🔴 خطا")
    else:
        statuses.append("🟢 دریافت شد")
    prices.append(price)

df = pd.DataFrame(assets)
df["قیمت_لحظه‌ای"] = prices
df["وضعیت"] = statuses
df["ارزش_تومان"] = df["count"] * df["قیمت_لحظه‌ای"]

total_value = df["ارزش_تومان"].sum()

# ========== نمایش داشبورد ==========
col1, col2 = st.columns(2)
with col1:
    st.metric("💰 ارزش کل سبد", f"{total_value:,.0f} تومان")
with col2:
    st.metric("🕒 آخرین بروزرسانی", datetime.now().strftime('%H:%M:%S'))

st.subheader("📋 لیست دارایی‌ها")
display_df = df[["name", "count", "قیمت_لحظه‌ای", "unit", "ارزش_تومان", "source", "وضعیت"]]
display_df.columns = ["دارایی", "تعداد", "قیمت (تومان)", "واحد", "ارزش (تومان)", "منبع", "وضعیت"]

st.dataframe(
    display_df,
    column_config={
        "قیمت (تومان)": st.column_config.NumberColumn(format="%.0f"),
        "ارزش (تومان)": st.column_config.NumberColumn(format="%.0f")
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

zero_assets = df[df["ارزش_تومان"] == 0]["name"].tolist()
if zero_assets:
    st.warning(f"⚠️ دارایی‌های زیر ارزش صفر دارند: {', '.join(zero_assets)}")
    st.info("💡 برای به‌روز کردن قیمت این دارایی‌ها، فایل `prices.json` را در گیت‌هاب ویرایش کنید.")

st.success("✅ قیمت طلا و دلار از Navasan، بیت‌کوین از CoinGecko و قیمت سهام از فایل JSON دریافت می‌شود.")
