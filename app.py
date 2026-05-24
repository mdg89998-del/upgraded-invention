import streamlit as st
import pandas as pd
import pandas_ta_classic as ta
import yfinance as yf
import FinanceDataReader as fdr

# 페이지 설정은 맨 위에 딱 한 번만!
st.set_page_config(page_title="AI STOCK", layout="centered")

st.title("📱 AI 자산 전광판")

# 1. 종목 검색 기능 (통합)
@st.cache_data
def get_stock_list():
    df_krx = fdr.StockListing('KRX')
    return df_krx[['Code', 'Name', 'Market']]

stock_list = get_stock_list()

st.write("### 🔍 종목 검색")
search_query = st.selectbox("종목명을 검색하세요:", stock_list['Name'], key="main_search")

# 선택 종목 처리
selected_row = stock_list[stock_list['Name'] == search_query].iloc[0]
ticker = f"{selected_row['Code']}.KS" if selected_row['Market'] == 'KOSPI' else f"{selected_row['Code']}.KQ"

if st.button("분석 실행"):
    data = yf.download(ticker, period="6mo")
    if not data.empty:
        st.line_chart(data['Close'])
    else:
        st.error("데이터를 찾을 수 없습니다.")

st.write("---")
st.write("### 📋 관심 종목 현황")

# 2. 기존 관심 종목 리스트
watchlist = {
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "현대차": "005380.KS",
    "테슬라": "TSLA", "애플": "AAPL", "엔비디아": "NVDA"
}

for name, ticker in sorted(watchlist.items()):
    try:
        df = yf.Ticker(ticker).history(period="6mo")
        if df.empty: continue
        
        df["RSI"] = ta.rsi(df["Close"], length=14)
        rsi = df["RSI"].iloc[-1]
        c_pr = df["Close"].iloc[-1]
        
        sig = "🔥 강력매수" if rsi <= 30 else ("🔵 관망")
        t_txt = f"{name} | ${c_pr:,.0f} | {sig}"
        
        with st.expander(t_txt):
            st.write(f"RSI: {rsi:.1f}")
            st.line_chart(df['Close'].tail(30))
    except Exception:
        continue