import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 데이터 로드 함수
@st.cache_data
def get_data(code, interval):
    df = fdr.DataReader(code, '2020-01-01')
    if interval == '주봉':
        df = df.resample('W').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
    elif interval == '월봉':
        df = df.resample('ME').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
    return df.dropna()

def main():
    st.set_page_config(page_title="AI PRO ANALYZER", layout="wide")
    
    # 종목 리스트 로드
    try: stock_list = fdr.StockListing('KRX')[['Code', 'Name']]
    except: stock_list = pd.DataFrame({'Code': ['005930'], 'Name': ['삼성전자']})

    # 사이드바
    with st.sidebar:
        query = st.text_input("종목 검색")
        filtered = stock_list[stock_list['Name'].str.contains(query, na=False)] if query else stock_list
        selected = st.selectbox("검색 결과", filtered['Name'], key="selector")
        interval = st.radio("차트 주기", ["일봉", "주봉", "월봉"], horizontal=True)

    # 데이터 가져오기
    code = stock_list[stock_list['Name'] == selected]['Code'].values[0]
    df = get_data(code, interval)

    if df.empty:
        st.error("데이터 로드 오류: 종목을 다시 선택해주세요.")
        return

    st.title(f"📈 {selected} ({interval})")

    # 2. 요약 정보창
    curr, prev = df['Close'].iloc[-1], df['Close'].iloc[-2]
    vol_curr, vol_prev = df['Volume'].iloc[-1], df['Volume'].iloc[-2]
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("현재가", f"{int(curr):,}원", f"{int(curr-prev):,} ({(curr-prev)/prev*100:.2f}%)")
    c2.metric("거래량", f"{int(vol_curr):,}", f"{((vol_curr-vol_prev)/vol_prev)*100:+.1f}% 전일비")
    c3.metric("고가", f"{int(df['High'].iloc[-1]):,}원")
    c4.metric("저가", f"{int(df['Low'].iloc[-1]):,}원")
    st.write("---")

    # 3. AI 알고리즘 매매 추종 (5단계 진단)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs.iloc[-1]))
    
    st.subheader("🤖 AI 알고리즘 실시간 진단")
    if rsi < 20: signal, color, desc = "1단계 (강력 매수)", "red", "과매도 구간: 기술적 반등 기대"
    elif rsi < 40: signal, color, desc = "2단계 (매수)", "orange", "저평가 구간: 분할 매수 적기"
    elif rsi < 60: signal, color, desc = "3단계 (관망)", "gray", "박스권 유지: 추세 전환 확인 필요"
    elif rsi < 80: signal, color, desc = "4단계 (매도)", "blue", "과열 구간: 차익 실현 권장"
    else: signal, color, desc = "5단계 (강력 매도)", "purple", "버블 구간: 위험 관리 필수"
    
    st.markdown(f"### <span style='color:{color}'>{signal}</span>", unsafe_allow_html=True)
    st.info(f"RSI: {rsi:.2f} | {desc}")

    # 4. 차트 생성
    for i in [5, 20, 40, 60]: df[f'MA{i}'] = df['Close'].rolling(window=i).mean()
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']), row=1, col=1)
    for ma in [5, 20, 40, 60]: fig.add_trace(go.Scatter(x=df.index, y=df[f'MA{ma}'], name=f'MA{ma}'), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['Volume']), row=2, col=1)
    fig.update_layout(xaxis_rangeslider_visible=False, height=500, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

if __name__ == '__main__':
    main()