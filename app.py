import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 안정적인 데이터 로드
@st.cache_data(ttl=86400)
def get_stock_list():
    try:
        df = fdr.StockListing('KRX')[['Code', 'Name']]
    except:
        df = pd.DataFrame({'Code': ['005930', '000660', '035420', '005380'], 
                           'Name': ['삼성전자', 'SK하이닉스', 'NAVER', '현대차']})
    return df

def main():
    st.set_page_config(page_title="AI PRO ANALYZER", layout="wide")
    stock_df = get_stock_list()
    name_to_code = dict(zip(stock_df['Name'], stock_df['Code']))

    # 2. 사이드바
    with st.sidebar:
        st.subheader("🔍 종목 찾기")
        query = st.text_input("종목명 입력")
        filtered_names = [name for name in name_to_code.keys() if query in name] if query else list(name_to_code.keys())
        selected = st.selectbox("검색 결과", filtered_names)
        interval = st.radio("차트 주기", ["일봉", "주봉", "월봉"], horizontal=True)

    # 3. 데이터 로드 및 계산
    target_code = name_to_code.get(selected, '005930')
    df = fdr.DataReader(target_code, '2020-01-01')
    if interval == '주봉':
        df = df.resample('W').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
    elif interval == '월봉':
        df = df.resample('ME').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
    df = df.dropna()

    st.title(f"📈 {selected} ({interval})")

    # 4. 정보창 (가격 + 전일비 거래량 + 고저가)
    if len(df) >= 2:
        curr, prev = df['Close'].iloc[-1], df['Close'].iloc[-2]
        vol_curr, vol_prev = df['Volume'].iloc[-1], df['Volume'].iloc[-2]
        vol_rate = ((vol_curr - vol_prev) / vol_prev) * 100
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("현재가", f"{int(curr):,}원", f"{int(curr-prev):,} ({(curr-prev)/prev*100:.2f}%)")
        # 거래량 전일비 추가!
        c2.metric("거래량", f"{int(vol_curr):,}", f"{vol_rate:+.1f}% 전일비")
        c3.metric("고가", f"{int(df['High'].iloc[-1]):,}원")
        c4.metric("저가", f"{int(df['Low'].iloc[-1]):,}원")
        st.write("---")

        # AI 5단계 진단
        delta = df['Close'].diff()
        rsi = 100 - (100 / (1 + (delta.where(delta > 0, 0).rolling(14).mean() / (-delta.where(delta < 0, 0).rolling(14).mean()))))
        val = rsi.iloc[-1]
        
        st.subheader("🤖 AI 알고리즘 진단")
        col_a, col_b = st.columns([1, 3])
        if val < 20: col_a.error("1단계: 강력 매수"); col_b.info("강력한 과매도 상태입니다.")
        elif val < 40: col_a.warning("2단계: 매수"); col_b.info("저평가 구간으로 분할 매수가 유효합니다.")
        elif val < 60: col_a.info("3단계: 관망"); col_b.info("박스권 구간입니다. 추세를 기다리세요.")
        elif val < 80: col_a.warning("4단계: 매도"); col_b.info("단기 과열입니다. 수익을 확정하세요.")
        else: col_a.error("5단계: 강력 매도"); col_b.info("버블 위험 구간입니다. 리스크 관리가 최우선입니다.")
        st.write("---")

    # 5. 차트
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['Volume']), row=2, col=1)
    fig.update_layout(height=500, template="plotly_white", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

if __name__ == '__main__':
    main()