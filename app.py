import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="AI PRO ANALYZER", layout="wide")

@st.cache_data(ttl=86400)
def get_stock_data():
try:
df = fdr.StockListing("KRX")[["Code", "Name"]]
df["Code"] = df["Code"].astype(str)
return df
except:
return pd.DataFrame({
"Code": ["005930"],
"Name": ["삼성전자"]
})

def calculate_rsi(close, period=14):
delta = close.diff()

```
gain = delta.where(delta > 0, 0)
loss = -delta.where(delta < 0, 0)

avg_gain = gain.rolling(period).mean()
avg_loss = loss.rolling(period).mean()

rs = avg_gain / avg_loss
rsi = 100 - (100 / (1 + rs))

return rsi
```

stock_df = get_stock_data()

st.sidebar.title("🔍 종목 검색")

query = st.sidebar.text_input(
"종목명 또는 코드 입력",
""
)

if query:
filtered_df = stock_df[
stock_df["Name"].str.contains(
query,
case=False,
na=False
)
|
stock_df["Code"].str.contains(
query,
na=False
)
].copy()
else:
filtered_df = stock_df.copy()

filtered_df = filtered_df.head(100)

if filtered_df.empty:
st.warning("검색된 종목이 없습니다.")
st.stop()

filtered_df["display"] = (
filtered_df["Name"]
+ " ("
+ filtered_df["Code"]
+ ")"
)

selected_display = st.sidebar.selectbox(
"종목 선택",
filtered_df["display"]
)

selected_row = filtered_df[
filtered_df["display"]
== selected_display
].iloc[0]

selected_name = selected_row["Name"]
target_code = selected_row["Code"]

interval = st.sidebar.radio(
"차트 주기",
["일봉", "주봉", "월봉"]
)

try:
df = fdr.DataReader(
target_code,
"2023-01-01"
)

```
if interval == "주봉":
    df = df.resample("W").agg({
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
        "Volume": "sum"
    })

elif interval == "월봉":
    df = df.resample("M").agg({
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
        "Volume": "sum"
    })
```

except Exception as e:
st.error(f"데이터 오류: {e}")
st.stop()

df["MA5"] = df["Close"].rolling(5).mean()
df["MA20"] = df["Close"].rolling(20).mean()
df["RSI"] = calculate_rsi(df["Close"])

curr = df["Close"].iloc[-1]
prev = df["Close"].iloc[-2]

price_diff = (
((curr - prev) / prev) * 100
if prev != 0 else 0
)

rsi = df["RSI"].iloc[-1]
if np.isnan(rsi):
rsi = 50

st.title(f"📈 {selected_name}")

c1, c2, c3 = st.columns(3)

c1.metric(
"현재가",
f"{int(curr):,}원",
f"{price_diff:+.2f}%"
)

c2.metric(
"RSI",
f"{rsi:.1f}"
)

c3.metric(
"종목코드",
target_code
)

fig = go.Figure()

fig.add_trace(
go.Candlestick(
x=df.index,
open=df["Open"],
high=df["High"],
low=df["Low"],
close=df["Close"],
name="캔들"
)
)

fig.add_trace(
go.Scatter(
x=df.index,
y=df["MA5"],
name="MA5"
)
)

fig.add_trace(
go.Scatter(
x=df.index,
y=df["MA20"],
name="MA20"
)
)

fig.update_layout(
height=700,
xaxis_rangeslider_visible=False
)

st.plotly_chart(
fig,
use_container_width=True
)
