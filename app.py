import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# --------------------------------
# 페이지 설정
# --------------------------------
st.set_page_config(
    page_title="AI PRO ANALYZER",
    layout="wide"
)

# --------------------------------
# 다크 테마 CSS
# --------------------------------
st.markdown("""
<style>
html, body, [class*="css"] {
    background-color: #0E1117;
    color: white;
}

section[data-testid="stSidebar"] {
    background-color: #111827;
}

.stMetric {
    background-color: #1F2937;
    padding: 15px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------
# 종목 데이터
# --------------------------------
@st.cache_data(ttl=86400)
def get_stock_data():
    try:
        df = fdr.StockListing("KRX")[["Code", "Name"]]
        df["Code"] = df["Code"].astype(str)
        return df
    except Exception:
        return pd.DataFrame({
            "Code": ["005930"],
            "Name": ["삼성전자"]
        })

# --------------------------------
# RSI 계산
# --------------------------------
def calculate_rsi(close, period=14):
    delta = close.diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi

# --------------------------------
# MACD 계산
# --------------------------------
def calculate_macd(close):
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()

    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    hist = macd - signal

    return macd, signal, hist

# --------------------------------
# 종목 검색
# --------------------------------
stock_df = get_stock_data()

st.sidebar.title("🔍 종목 검색")

query = st.sidebar.text_input(
    "종목명 또는 종목코드",
    placeholder="예: 삼성, SK, 005930"
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
    filtered_df["display"] == selected_display
].iloc[0]

selected_name = selected_row["Name"]
target_code = selected_row["Code"]

# --------------------------------
# 차트 주기
# --------------------------------
interval = st.sidebar.radio(
    "차트 주기",
    ["일봉", "주봉", "월봉"],
    horizontal=True
)

# --------------------------------
# 데이터 가져오기
# --------------------------------
try:
    df = fdr.DataReader(
        target_code,
        "2023-01-01"
    )

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

    df.dropna(inplace=True)

except Exception as e:
    st.error(f"데이터 오류: {e}")
    st.stop()

# --------------------------------
# 보조지표 계산
# --------------------------------
df["MA5"] = df["Close"].rolling(5).mean()
df["MA20"] = df["Close"].rolling(20).mean()
df["MA60"] = df["Close"].rolling(60).mean()

df["RSI"] = calculate_rsi(df["Close"])

macd, signal_line, hist = calculate_macd(df["Close"])

df["MACD"] = macd
df["Signal"] = signal_line
df["Hist"] = hist

curr = df["Close"].iloc[-1]
prev = df["Close"].iloc[-2]

price_diff = (
    ((curr - prev) / prev) * 100
    if prev != 0 else 0
)

vol_curr = df["Volume"].iloc[-1]
vol_prev = df["Volume"].iloc[-2]

vol_diff = (
    ((vol_curr - vol_prev) / vol_prev) * 100
    if vol_prev != 0 else 0
)

rsi = df["RSI"].iloc[-1]
if np.isnan(rsi):
    rsi = 50

st.title(f"📈 {selected_name}")

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "현재가",
    f"{int(curr):,}원",
    f"{price_diff:+.2f}%"
)

c2.metric(
    "거래량",
    f"{int(vol_curr):,}",
    f"{vol_diff:+.2f}%"
)

c3.metric(
    "RSI",
    f"{rsi:.1f}"
)

c4.metric(
    "종목코드",
    target_code
)# --------------------------------
# AI 진단
# --------------------------------
golden_cross = (
    df["MA5"].iloc[-2] < df["MA20"].iloc[-2]
    and
    df["MA5"].iloc[-1] > df["MA20"].iloc[-1]
)

dead_cross = (
    df["MA5"].iloc[-2] > df["MA20"].iloc[-2]
    and
    df["MA5"].iloc[-1] < df["MA20"].iloc[-1]
)

signal_text = "관망"
signal_color = "#9CA3AF"
desc = "특별한 신호가 없습니다."

if golden_cross and rsi < 70:
    signal_text = "강력 매수"
    signal_color = "#22C55E"
    desc = "골든크로스 발생 + RSI 양호"

elif dead_cross:
    signal_text = "매도 주의"
    signal_color = "#EF4444"
    desc = "데드크로스 발생"

elif rsi < 30:
    signal_text = "저점 매수"
    signal_color = "#F59E0B"
    desc = "과매도 구간"

elif rsi > 75:
    signal_text = "과열"
    signal_color = "#EF4444"
    desc = "단기 과열 가능성"

st.markdown(
    f"""
    <div style='
        background:#111827;
        padding:20px;
        border-radius:15px;
        margin-top:10px;
        margin-bottom:20px;
    '>
        <h2 style='margin:0;color:white'>
        🎯 AI 진단:
        <span style='color:{signal_color}'>
        {signal_text}
        </span>
        </h2>

        <p style='color:#D1D5DB;font-size:16px'>
        {desc} | RSI: {rsi:.1f}
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# --------------------------------
# 거래량 색상
# --------------------------------
volume_colors = np.where(
    df["Close"] >= df["Open"],
    "#EF4444",   # 상승 빨강
    "#3B82F6"    # 하락 파랑
)

hist_colors = np.where(
    df["Hist"] >= 0,
    "#22C55E",
    "#EF4444"
)

# --------------------------------
# 차트 생성
# --------------------------------
fig = make_subplots(
    rows=4,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.02,
    row_heights=[0.55, 0.15, 0.15, 0.15]
)

# 캔들
fig.add_trace(
    go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        increasing_line_color="#EF4444",
        decreasing_line_color="#3B82F6",
        increasing_fillcolor="#EF4444",
        decreasing_fillcolor="#3B82F6",
        name="가격"
    ),
    row=1,
    col=1
)

# 이동평균선
fig.add_trace(
    go.Scatter(
        x=df.index,
        y=df["MA5"],
        name="MA5",
        line=dict(color="#FACC15", width=1.5)
    ),
    row=1,
    col=1
)

fig.add_trace(
    go.Scatter(
        x=df.index,
        y=df["MA20"],
        name="MA20",
        line=dict(color="#22C55E", width=1.5)
    ),
    row=1,
    col=1
)

fig.add_trace(
    go.Scatter(
        x=df.index,
        y=df["MA60"],
        name="MA60",
        line=dict(color="#A855F7", width=1.5)
    ),
    row=1,
    col=1
)

# 거래량
fig.add_trace(
    go.Bar(
        x=df.index,
        y=df["Volume"],
        marker_color=volume_colors,
        name="거래량"
    ),
    row=2,
    col=1
)

# RSI
fig.add_trace(
    go.Scatter(
        x=df.index,
        y=df["RSI"],
        line=dict(color="#38BDF8"),
        name="RSI"
    ),
    row=3,
    col=1
)

fig.add_hline(
    y=70,
    line_dash="dash",
    line_color="red",
    row=3,
    col=1
)

fig.add_hline(
    y=30,
    line_dash="dash",
    line_color="green",
    row=3,
    col=1
)

# MACD
fig.add_trace(
    go.Scatter(
        x=df.index,
        y=df["MACD"],
        line=dict(color="#60A5FA"),
        name="MACD"
    ),
    row=4,
    col=1
)

fig.add_trace(
    go.Scatter(
        x=df.index,
        y=df["Signal"],
        line=dict(color="#F97316"),
        name="Signal"
    ),
    row=4,
    col=1
)

fig.add_trace(
    go.Bar(
        x=df.index,
        y=df["Hist"],
        marker_color=hist_colors,
        name="Histogram"
    ),
    row=4,
    col=1
)

# --------------------------------
# 차트 스타일
# --------------------------------
fig.update_layout(
    template="plotly_dark",
    height=1100,
    dragmode="zoom",
    hovermode="x unified",
    xaxis_rangeslider_visible=False,
    paper_bgcolor="#0E1117",
    plot_bgcolor="#0E1117",
    font=dict(color="white"),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
    margin=dict(
        l=20,
        r=20,
        t=20,
        b=20
    )
)

fig.update_yaxes(
    showgrid=True,
    gridcolor="rgba(255,255,255,0.08)"
)

fig.update_xaxes(
    showgrid=False
)

st.plotly_chart(
    fig,
    use_container_width=True
)