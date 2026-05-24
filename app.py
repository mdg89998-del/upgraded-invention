import streamlit as st
import pandas as pd
import pandas_ta_classic as ta
import FinanceDataReader as fdr
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="AI MARKET BOARD", layout="wide")
st.title("🤖 AI 시장 위험 분석기")

# 1. 시장 데이터 수집 함수
@st.cache_data
def get_market_data():
    # 나스닥 100(NDX), 코스피(KS11), 코스닥(KQ11), VIX(^VIX)
    tickers = {"나스닥100": "^NDX", "코스피": "KS11", "코스닥": "KQ11", "VIX지수": "^VIX"}
    data = {}
    for name, ticker in tickers.items():
        df = yf.Ticker(ticker).history(period="1mo")
        data[name] = df['Close'].iloc[-1]
    return data

# 2. 시장 위험도 분석 로직 (3단계)
def analyze_risk(vix_val):
    if vix_val < 20: return "🟢 양호", "변동성이 낮아 시장이 안정적입니다."
    elif vix_val < 30: return "🟡 경계", "변동성이 커지고 있어 리스크 관리가 필요합니다."
    else: return "🔴 위험", "시장에 공포가 확산되는 구간입니다. 현금 확보를 권장합니다."

# 3. 시장 현황판 구성
market_data = get_market_data()
vix = market_data["VIX지수"]
status, desc = analyze_risk(vix)

col1, col2, col3, col4 = st.columns(4)
col1.metric("나스닥 100", f"{market_data['나스닥100']:,.0f}")
col2.metric("코스피", f"{market_data['코스피']:,.0f}")
col3.metric("코스닥", f"{market_data['코스닥']:,.0f}")
col4.metric("VIX 지수", f"{vix:.2f}", status)

st.subheader(f"📊 AI 종합 시장 진단: {status}")
st.write(f"**AI 알고리즘 분석:** {desc}")

st.write("---")
# (기존 종목 검색 및 AI 분석 기능은 아래에 그대로 이어서 붙이시면 됩니다.)