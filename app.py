import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
import os
from datetime import datetime

st.set_page_config(page_title="سبد پویا", layout="centered")
st.title("📊 سبد مادر (خودکار + دستی + میانگین خرید)")

DATA_FILE = "portfolio_data.json"
PRICES_FILE = "prices.json"

# ---------- لیست سهام‌های نهایی (ادغام از ۴ پرتفوی) ----------
NEW_STOCKS = [
    {"name": "سمگا", "count": 32071, "unit": "سهم", "buy_price": 383.5},
    {"name": "فروی‌ح", "count": 100000, "unit": "سهم", "buy_price": 84.1},
    {"name": "آبادا", "count": 8135, "unit": "سهم", "buy_price": 1182.8},
    {"name": "اوند", "count": 2000, "unit": "سهم", "buy_price": 4421.6},
    {"name": "وصنعت", "count": 30000, "unit": "سهم", "buy_price": 116.1},
    {"name": "ولیز", "count": 9367, "unit": "سهم", "buy_price": 470.4},
    {"name": "هانیکو", "count": 2489, "unit": "سهم", "buy_price": 906.4},
    {"name": "نقران", "count": 36049, "unit": "سهم", "buy_price": 1320.4},
    {"name": "فنفت", "count": 37190, "unit": "سهم", "buy_price": 436.6},
    {"name": "خشکست", "count": 122234, "unit": "سهم", "buy_price": 141.4},
    {"name": "فروخت", "count": 119946, "unit": "سهم", "buy_price": 75.7},
    {"name": "مروگان", "count": 4098, "unit": "سهم", "buy_price": 947.2},
    {"name": "اطلس", "count": 3346, "unit": "سهم", "buy_price": 14263.6},
    {"name": "عیار", "count": 2289, "unit": "سهم", "buy_price": 24705.7},
    {"name": "اروند", "count": 3089, "unit": "سهم", "buy_price": 4624.4},
    {"name": "آکو", "count": 915, "unit": "سهم", "buy_price": 3344},
    {"name": "خزاعیا", "count": 60601, "unit": "سهم", "buy_price": 76.7},
    {"name": "اخابر", "count": 285000, "unit": "سهم", "buy_price": 61.8},
    {"name": "غریجی", "count": 31209, "unit": "سهم", "buy_price": 180.2},
    {"name": "اممر", "count": 2000, "unit": "سهم", "buy_price": 5193.6},
    {"name": "فارماکیان", "count": 4000, "unit": "سهم", "buy_price": 1005.8}
]

# ---------- دریافت خودکار قیمت‌ها ----------
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
    default_assets = [
        {"name": "طلا ۱۸", "count": 45, "unit": "گرم", "buy_price": 0},
        {"name": "دلار", "count": 1800, "unit": "دلار", "buy_price": 0},
        {"name": "بیت‌کوین", "count": 0.007025, "unit": "BTC", "buy_price": 0},
        {"name": "نقد", "count": 500000000, "unit": "تومان", "buy_price": 1}
    ]
    default_assets.extend(NEW_STOCKS)
    
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
            existing_names = [a["name"] for a in saved["assets"]]
            for stock in NEW_STOCKS:
                if stock["name"] not in existing_names:
                    saved["assets"].append(stock)
            return saved
    else:
        return {"assets": default_assets}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ========== بارگذاری ==========
data = load_data()
assets = data["assets"]
prices = load_prices()

# ---------- دریافت خودکار (با نگهداری قیمت قبلی در صورت خطا) ----------
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
    
    # ---------- بخش ۱: ورود قیمت‌های روزانه ----------
    st.subheader("📝 قیمت‌های روزانه")
    st.caption("قیمت‌ها را می‌توانید دستی وارد کنید (اگر خودکار نیامد).")
    
    new_prices = {}
    for asset in assets:
        name = asset["name"]
        if name == "نقد":
            new_prices[name] = 1
            continue
        
        current = prices.get(name, 0)
        if name in ["دلار", "طلا ۱۸", "بیت‌کوین"]:
            st.info(f"🟢 {name}: {current:,.0f} تومان (خودکار - در صورت نیاز ویرایش کنید)")
        
        new_price = st.number_input(
            f"{name} (هر {asset['unit']})",
            min_value=0,
            value=current,
            step=100 if name != "بیت‌کوین" else 1000000,
            key=f"price_{name}"
        )
        new_prices[name] = new_price
    
    if st.button("💾 ذخیره قیمت‌ها"):
        save_prices(new_prices)
        st.success("✅ قیمت‌ها ذخیره شدند!")
        st.rerun()
    
    st.divider()
    
    # ---------- بخش ۲: ویرایش دارایی (نام، تعداد، قیمت خرید) ----------
    st.subheader("✏️ ویرایش دارایی")
    
    if len(assets) > 0:
        selected_name = st.selectbox("انتخاب دارایی برای ویرایش", [a["name"] for a in assets])
        selected = next(a for a in assets if a["name"] == selected_name)
        
        # تغییر نام
        new_name = st.text_input(
            "نام جدید (در صورت تغییر)",
            value=selected["name"],
            key=f"edit_name_{selected_name}"
        )
        
        # تغییر تعداد
        new_count = st.number_input(
            "تعداد جدید",
            min_value=0.0,
            step=0.01,
            value=float(selected["count"]),
            key=f"edit_count_{selected_name}"
        )
        
        # تغییر قیمت خرید (با محاسبه میانگین وزنی)
        new_buy_price = st.number_input(
            "قیمت خرید جدید (برای هر واحد - در صورت اضافه کردن)",
            min_value=0,
            value=0,
            step=1000,
            key=f"edit_buy_{selected_name}",
            help="اگر تعداد جدید اضافه می‌کنید، قیمت خرید جدید را وارد کنید تا میانگین محاسبه شود."
        )
        
        # محاسبه میانگین وزنی
        if new_buy_price > 0 and new_count > 0:
            old_count = selected["count"]
            old_buy = selected["buy_price"]
            if old_count == 0:
                avg_buy = new_buy_price
            else:
                avg_buy = (old_count * old_buy + new_count * new_buy_price) / (old_count + new_count)
            st.info(f"💰 قیمت میانگین خرید جدید: {avg_buy:,.0f} تومان")
        else:
            avg_buy = selected["buy_price"]
        
        # دکمه ذخیره
        if st.button("💾 ذخیره تغییرات", key=f"save_edit_{selected_name}"):
            # بررسی تکراری نبودن نام جدید
            name_changed = (new_name != selected["name"])
            if name_changed:
                existing_names = [a["name"] for a in assets if a["name"] != selected["name"]]
                if new_name in existing_names:
                    st.error(f"❌ نام '{new_name}' قبلاً در سبد وجود دارد. لطفاً نام دیگری انتخاب کنید.")
                    st.stop()
            
            # اعمال تغییرات
            for a in assets:
                if a["name"] == selected["name"]:
                    if name_changed:
                        old_price = prices.pop(selected["name"], 0)
                        if old_price:
                            prices[new_name] = old_price
                        a["name"] = new_name
                    
                    a["count"] = new_count
                    if new_buy_price > 0 and new_count > 0:
                        a["buy_price"] = avg_buy
                    if new_count == 0:
                        a["buy_price"] = 0
                    break
            
            save_data(data)
            save_prices(prices)
            st.success("✅ تغییرات ذخیره شد!")
            st.rerun()
        
        st.caption(f"💰 قیمت خرید فعلی: {selected['buy_price']:,.0f} تومان")
    
    st.divider()
    
    # ---------- بخش ۳: اضافه کردن دارایی جدید ----------
    st.subheader("➕ اضافه کردن دارایی جدید")
    new_name = st.text_input("نام دارایی")
    new_count = st.number_input("تعداد", min_value=0.0, step=0.01, value=1.0)
    new_unit = st.text_input("واحد (مثلاً سهم، گرم)")
    new_buy = st.number_input("قیمت خرید (برای هر واحد)", min_value=0, value=0, step=1000)
    
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
        else:
            st.error("❌ نام و تعداد را وارد کنید.")
    
    st.divider()
    
    # ---------- بخش ۴: حذف دارایی ----------
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
    height=500
)

st.subheader("🎯 ترکیب سبد")
df_chart = df[df["ارزش_تومان"] > 0].copy()
if len(df_chart) > 0:
    fig = px.pie(df_chart, values="ارزش_تومان", names="name", hole=0.4)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("هیچ دارایی با ارزش مثبت وجود ندارد.")

st.caption("💡 قیمت‌ها را می‌توانید دستی وارد کنید یا از خودکار استفاده کنید. برای ویرایش تعداد و قیمت خرید، از بخش ویرایش استفاده کنید.")
