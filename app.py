import pandas as pd
import pandas_ta_classic as ta
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="AI STOCK", layout="centered")
st.title("📱 AI 자산 전광판")
st.write("---")

watchlist = {
    "대한항공": "003490.KS", "동진쎄미켐": "005160.KQ", "두산에너빌리티": "034020.KS",
    "마이크로투나노": "424980.KQ", "삼성SDI": "006400.KS", "삼성전기": "009150.KS",
    "삼성전자": "005930.KS", "세미파이브": "490470.KQ", "신성이엔지": "011930.KS",
    "아이티센": "124500.KS", "원익IPS": "240810.KS", "원익QnC": "074600.KQ",
    "주성엔지니어링": "036930.KQ", "케이엔솔": "053080.KS", "켐트로닉스": "089010.KQ",
    "키움증권": "039490.KS", "필옵틱스": "161580.KQ", "현대차": "005380.KS",
    "LIG넥스원": "079550.KS", "HD현대일렉트릭": "043200.KS", "LG전자": "066570.KS",
    "SK하이닉스": "000660.KS", "SKC": "011790.KS", "델(DELL)": "DELL",
    "마이크론(MU)": "MU", "샌디스크(WDC)": "WDC", "써클(USDC)": "USDC-USD",
    "알파벳(GOOGL)": "GOOGL", "아이온큐(IONQ)": "IONQ", "AMD": "AMD",
    "인텔(INTC)": "INTC", "퀄컴(QCOM)": "QCOM", "테슬라(TSLA)": "TSLA",
    "비트코인(BTC)": "BTC-USD", "이더리움(ETH)": "ETH-USD"
}

with st.spinner("🔄 분석 중..."):
    for name, ticker in sorted(watchlist.items()):
        try:
            df = yf.Ticker(ticker).history(period="6mo")
            if df.empty or len(df) < 20: continue

            df["RSI"] = ta.rsi(df["Close"], length=14)
            df["E20"] = ta.ema(df["Close"], length=20)
            df["E60"] = ta.ema(df["Close"], length=60)
            df.dropna(subset=["RSI", "E20", "E60"], inplace=True)
            if df.empty: continue

            c_pr = df["Close"].iloc[-1]
            p_pr = df["Close"].iloc[-2]
            pct = ((c_pr - p_pr) / p_pr) * 100
            rsi = df["RSI"].iloc[-1]
            bull = bool(df["E20"].iloc[-1] > df["E60"].iloc[-1])

            p_fmt = f"${c_pr:,.1f}" if c_pr < 1000 else f"{int(c_pr):,}원"
            if "BTC" in ticker: p_fmt = f"${c_pr:,.0f}"

            sig = "🔥 강력매수" if rsi <= 30 else ("🟢 과매도" if rsi <= 35 else ("🔴 과매수" if rsi >= 70 else "🔵 관망"))
            trend = "📈 정배열" if bull else "📉 역배열"

            t_txt = f"{name} | {p_fmt} ({pct:+.1f}%) | {sig}"
            
            with st.expander(t_txt):
                st.write(f"🚦 AI 상태 진단: **{sig}** (RSI: {rsi:.1f})")
                st.write(f"📈 이동평균선 흐름: **{trend}**")
                
                c_df = df[['Close', 'E20', 'E60']].tail(60).copy()
                c_df.columns = ['Close', 'EMA20', 'EMA60']
                st.line_chart(c_df, use_container_width=True)
        except Exception:
            continue

st.success("✅ 완료! 종목 카드를 누르면 차트가 정상적으로 열립니다.")
import streamlit as st
import yfinance as yf
import FinanceDataReader as fdr

st.title("📈 나만의 주식 검색 전광판")

# 1. 코스피/코스닥 종목 리스트 가져오기 (매번 가져오지 않도록 캐싱 사용)
@st.cache_data
def get_stock_list():
    df_krx = fdr.StockListing('KRX')
    return df_krx[['Code', 'Name']]

stock_list = get_stock_list()

# 2. 검색창 만들기 (종목명으로 검색)
search_query = st.selectbox("종목명을 검색하세요:", stock_list['Name'])

# 선택한 종목의 코드 찾기
ticker_code = stock_list[stock_list['Name'] == search_query]['Code'].values[0]
# 야후 파이낸스용 티커 변환 (코스피/코스닥에 따라 .KS 또는 .KQ 붙임)
# (이 부분은 종목 코드 뒤에 .KS나 .KQ를 붙여야 정확히 검색됩니다)

st.write(f"선택하신 종목: {search_query} ({ticker_code})")

# 3. 데이터 불러오기 및 시각화 (기존 코드 유지)
# 여기에 기존에 쓰시던 yfinance 데이터 불러오기 코드를 연결하세요!import streamlit as st
import yfinance as yf
import FinanceDataReader as fdr

st.title("📈 나만의 주식 검색 전광판")

@st.cache_data
def get_stock_list():
    df_krx = fdr.StockListing('KRX')
    return df_krx[['Code', 'Name', 'Market']] # 'Market' 정보 추가

stock_list = get_stock_list()

search_query = st.selectbox("종목명을 검색하세요:", stock_list['Name'])

# 선택한 종목의 코드와 시장 정보 가져오기
selected_row = stock_list[stock_list['Name'] == search_query].iloc[0]
ticker_code = selected_row['Code']
market = selected_row['Market']

# 야후 파이낸스 티커 형식으로 변환 (KOSPI는 .KS, KOSDAQ은 .KQ)
suffix = ".KS" if market == 'KOSPI' else ".KQ"
ticker = f"{ticker_code}{suffix}"

st.write(f"선택하신 종목: {search_query} ({ticker})")

# 데이터 불러오기
data = yf.download(ticker, period='1mo') # 최근 1개월 데이터

if not data.empty:
    st.line_chart(data['Close'])
else:
    st.error("데이터를 불러올 수 없습니다. 코드 형식을 확인하세요.")
# 수정 전
search_query = st.selectbox("종목명을 검색하세요:", stock_list['Name'])

# 수정 후 (아래처럼 key="stock_search_selectbox"를 추가하세요)
search_query = st.selectbox("종목명을 검색하세요:", stock_list['Name'], key="stock_search_selectbox")
