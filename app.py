import streamlit as st
import pandas as pd
import pandas_ta_classic as ta
import FinanceDataReader as fdr
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

st.set_page_config(page_title="AI PRO ANALYZER", layout="wide")

# 세션 상태 초기화
if 'search_history' not in st.session_state:
    st.session_state.search_history = []

st.title("🤖 AI 프로 자산 분석기")

# 1. 데이터 로드 함수 (최적화)
@st.cache_data(ttl=3600)
def get_market_status():
    data = {}
    try:
        # FinanceDataReader로 안정적 지수 로드
        data["나스닥100"] = fdr.DataReader("NDX", datetime.now()-timedelta(days=7))['Close'].iloc[-1]
        data["코스피"] = fdr.DataReader("KS11", datetime.now()-timedelta(days=7))['Close'].iloc[-1]
        data["코스닥"] = fdr.DataReader("KQ11", datetime.now()-timedelta(days=7))['Close'].iloc[-1]
        # VIX는 yfinance (최소 요청)
        vix = yf.Ticker("^VIX").history(period="1d")
        data["VIX지수"] = vix['Close'].iloc[-1]
    except:
        data = {"나스닥100": 0, "코스피": 0, "코스닥": 0, "VIX지수": 20}
    return data

@st.cache_data
def get_stock_list():
    try: return fdr.StockListing('KRX')[['Code', 'Name']]
    except: return pd.DataFrame({'Code': ['005930'], 'Name': ['삼성전자']})

# 2. 시장 현황판 (상단)
market_data = get_market_status()
vix = market_data["VIX지수"]
risk_level = "🟢 양호" if vix < 20 else ("🟡 경계" if vix < 30 else "🔴 위험")

c1, c2, c3, c4 = st.columns(4)
c1.metric("나스닥 100", f"{market_data['나스닥100']:,.0f}")
c2.metric("코스피", f"{market_data['코스피']:,.0f}")
c3.metric("코스닥", f"{market_data['코스닥']:,.0f}")
c4.metric("VIX 지수", f"{vix:.2f}", risk_level)

st.write("---")

# 3. 사이드바 (검색 및 기록)
stock_list = get_stock_list()
with st.sidebar:
    search = st.selectbox("종목 검색", stock_list['Name'])
    if st.button("분석 실행"):
        if search not in st.session_state.search_history:
            st.session_state.search_history.insert(0, search)
            if len(st.session_state.search_history) > 10: st.session_state.search_history.pop()
    
    st.write("### 🕒 최근 검색 (10개)")
    for item in st.session_state.search_history: st.caption(f"🔹 {item}")

# 4. 분석 엔진 및 차트
code = stock_list[stock_list['Name'] == search]['Code'].values[0]
df = fdr.DataReader(code, '2022-01-01')

for i in [5, 20, 60, 120]: df[f'MA{i}'] = ta.ema(df['Close'], length=i)
df['RSI'] = ta.rsi(df['Close'], length=14)

fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='시세'), row=1, col=1)
for i in [5, 20, 60, 120]: fig.add_trace(go.Scatter(x=df.index, y=df[f'MA{i}'], name=f'MA{i}'), row=1, col=1)
fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='거래량'), row=2, col=1)
st.plotly_chart(fig, use_container_width=True)

# 5. AI 진단
rsi = df['RSI'].iloc[-1]
st.subheader(f"🧠 AI 알고리즘 진단: {search}")
if rsi < 20: st.info(f"1단계 (강력매수): 과매도 구간입니다. (RSI: {rsi:.1f})")
elif rsi < 40: st.info(f"2단계 (매수): 저평가 구간입니다. (RSI: {rsi:.1f})")
elif rsi < 60: st.info(f"3단계 (관망): 박스권 구간입니다. (RSI: {rsi:.1f})")
elif rsi < 80: st.info(f"4단계 (매도): 과열 구간입니다. (RSI: {rsi:.1f})")
else: st.warning(f"5단계 (강력매도): 버블 구간입니다! (RSI: {rsi:.1f})")