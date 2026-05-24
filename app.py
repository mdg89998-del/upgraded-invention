import streamlit as st
import pandas as pd
import pandas_ta_classic as ta
import FinanceDataReader as fdr
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="AI PRO ANALYZER", layout="wide")
st.title("🤖 AI 프로 자산 분석기")

# 1. 종목 검색 및 기간/주기 설정
@st.cache_data
def get_stock_list():
    return fdr.StockListing('KRX')[['Code', 'Name']]

stock_list = get_stock_list()
col1, col2, col3 = st.columns([2, 1, 1])
with col1: search = st.selectbox("종목 검색", stock_list['Name'])
with col2: period = st.selectbox("기간", ["1y", "3y", "5y"])
with col3: interval = st.selectbox("주기", ["일봉", "주봉", "월봉"])

code = stock_list[stock_list['Name'] == search]['Code'].values[0]
interval_map = {"일봉": "1d", "주봉": "1w", "월봉": "1m"}

# 데이터 로드
df = fdr.DataReader(code, '2020-01-01') # 더 길게 가져오기
# 주봉/월봉 변환 로직 생략(간소화)

# 2. AI 지표 계산 (이동평균선 & RSI)
for i in [5, 20, 60, 120]:
    df[f'MA{i}'] = ta.ema(df['Close'], length=i)
df['RSI'] = ta.rsi(df['Close'], length=14)

# 3. 차트 시각화 (거래량 포함)
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='시세'), row=1, col=1)
for i in [5, 20, 60, 120]:
    fig.add_trace(go.Scatter(x=df.index, y=df[f'MA{i}'], name=f'MA{i}'), row=1, col=1)
fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='거래량'), row=2, col=1)
st.plotly_chart(fig, use_container_width=True)

# 4. AI 진단 로직 (5단계)
rsi = df['RSI'].iloc[-1]
def get_ai_signal(rsi):
    if rsi < 20: return "🔥 1단계: 강력매수 (극단적 저평가)", "과매도 구간으로 반등 가능성이 매우 높습니다."
    if rsi < 40: return "🟢 2단계: 매수 (저평가)", "상승 추세로 전환될 가능성이 있는 구간입니다."
    if rsi < 60: return "🔵 3단계: 관망", "현재 균형 잡힌 구간입니다."
    if rsi < 80: return "🔴 4단계: 매도 (과열)", "매수세가 강해 차익 실현을 고민해야 합니다."
    return "⚡ 5단계: 강력매도 (버블)", "과열 구간으로 조정 가능성이 매우 높습니다."

sig, reason = get_ai_signal(rsi)
st.write(f"### 🧠 AI 분석 결과: {sig}")
st.info(reason)

# 5. 수급 섹터 (간략화된 버전)
st.write("---")
st.write("### 📈 수급 현황 (섹터 모멘텀)")
# 실제로는 섹터 데이터 API가 필요하지만 여기서는 예시 코드를 제공합니다.
st.bar_chart(pd.DataFrame({'수급': [100, 85, 70, 50, 40]}, index=['반도체', '이차전지', '조선', '자동차', '금융']))