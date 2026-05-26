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
# ... (상단 코드 동일) ...

# 4. 분석 엔진 및 차트 (기존 내용)
code = stock_list[stock_list['Name'] == search]['Code'].values[0]
df = fdr.DataReader(code, '2022-01-01')

# 등락폭 계산 로직 추가
current_price = df['Close'].iloc[-1]
prev_price = df['Close'].iloc[-2]
change_val = current_price - prev_price
change_pct = (change_val / prev_price) * 100

# 시세와 등락폭 출력
st.subheader(f"📊 {search} 상세 시세")
col_a, col_b, col_c = st.columns(3)
col_a.metric("현재가", f"{int(current_price):,}원")
col_b.metric("등락폭", f"{int(change_val):,}원", f"{change_pct:.2f}%")
col_c.metric("거래량", f"{df['Volume'].iloc[-1]:,}")

# 차트 및 AI 진단 (아래는 기존과 동일)
import streamlit as st
import pandas as pd
import pandas_ta_classic as ta
import FinanceDataReader as fdr
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

st.set_page_config(page_title="AI PRO", layout="wide")

# 1. 데이터 로드 (에러 방지용)
@st.cache_data(ttl=3600)
def get_stock_list():
    try:
        df = fdr.StockListing('KRX')
        # 이름과 코드를 확실하게 매핑하기 위해 공백 제거
        df['Name_Clean'] = df['Name'].str.replace(" ", "").str.lower()
        return df[['Code', 'Name', 'Name_Clean']]
    except:
        return pd.DataFrame({'Code': ['005930'], 'Name': ['삼성전자'], 'Name_Clean': ['삼성전자']})

stock_list = get_stock_list()

# 2. 사이드바 (모바일에서는 접혀있어 편리합니다)
with st.sidebar:
    st.subheader("종목 선택")
    # 사용자가 입력한 검색어
    query = st.text_input("종목명 입력 (예: 삼성전자)")
    
    # 검색어에 맞는 종목 필터링
    filtered_list = stock_list[stock_list['Name'].str.contains(query, na=False)] if query else stock_list
    
    search = st.selectbox("검색 결과 선택", filtered_list['Name'])
    
    if st.button("분석 실행"):
        st.session_state.selected_stock = search

# 3. 분석 로직
if 'selected_stock' in st.session_state:
    target_name = st.session_state.selected_stock
    target_row = stock_list[stock_list['Name'] == target_name].iloc[0]
    code = target_row['Code']
    
    # 데이터 불러오기
    df = fdr.DataReader(code, '2022-01-01')
    
    # ... (지표 계산 및 차트 부분은 동일) ...
    st.success(f"{target_name} 분석 완료")