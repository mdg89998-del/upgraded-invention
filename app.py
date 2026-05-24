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
    import streamlit as st
import pandas as pd
import pandas_ta_classic as ta
import yfinance as yf
import FinanceDataReader as fdr

# 1. 페이지 설정
st.set_page_config(page_title="AI STOCK", layout="centered")
st.title("📈 AI 자산 검색 전광판")

# 2. 종목 리스트 가져오기 (캐싱)
@st.cache_data
def get_stock_list():
    df_krx = fdr.StockListing('KRX')
    return df_krx[['Code', 'Name']]

stock_list = get_stock_list()

# 3. 검색창
st.write("### 🔍 종목 검색")
search_query = st.selectbox("종목명을 검색하세요:", stock_list['Name'], key="main_search")

# 4. 분석 버튼
if st.button("분석 실행"):
    # 선택한 종목의 코드 추출
    ticker_code = stock_list[stock_list['Name'] == search_query]['Code'].values[0]
    
    with st.spinner(f"{search_query} 데이터 분석 중..."):
        # FinanceDataReader로 네이버 금융 기반 데이터 가져오기
        df = fdr.DataReader(ticker_code, '2026-01-01') 
        
        if not df.empty:
            st.success(f"{search_query} 분석 완료!")
            
            # 기술적 지표 계산
            df["RSI"] = ta.rsi(df["Close"], length=14)
            
            # 그래프 출력
            st.line_chart(df['Close'].tail(100)) # 최근 100일간의 종가
            
            # 상세 데이터
            st.write(f"최근 가격: {df['Close'].iloc[-1]:,}원")
            st.write(f"RSI 지표: {df['RSI'].iloc[-1]:.2f}")
        else:
            st.error("데이터를 가져올 수 없습니다.")

st.write("---")
st.write("### 📋 관심 종목 현황")
# (기존 관심 종목 리스트 로직 유지...)
