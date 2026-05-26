import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 데이터 로드 (캐시 사용)
@st.cache_data(ttl=3600)
def get_stock_data():
    df = fdr.StockListing('KRX')[['Code', 'Name']]
    # 매칭용 딕셔너리 생성 (Name: Code)
    name_to_code = dict(zip(df['Name'], df['Code']))
    return df, name_to_code

def main():
    st.set_page_config(page_title="AI PRO ANALYZER", layout="wide")
    stock_df, name_to_code = get_stock_data()

    # 2. 사이드바 (종목 검색)
    with st.sidebar:
        st.subheader("🔍 종목 찾기")
        query = st.text_input("종목명 검색")
        
        # 검색어 필터링
        if query:
            filtered_names = [name for name in name_to_code.keys() if query in name]
        else:
            filtered_names = list(name_to_code.keys())
            
        selected = st.selectbox("검색 결과", filtered_names)
        interval = st.radio("차트 주기", ["일봉", "주봉", "월봉"], horizontal=True)

    # 3. 데이터 로드 및 차트
    target_code = name_to_code[selected]
    
    # 데이터 로드 (주기에 따른 처리)
    df = fdr.DataReader(target_code, '2020-01-01')
    if interval == '주봉':
        df = df.resample('W').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
    elif interval == '월봉':
        df = df.resample('ME').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
    df = df.dropna()

    st.title(f"📈 {selected} ({interval})")

    # 정보창 (안전하게 계산)
    if len(df) >= 2:
        curr, prev = df['Close'].iloc[-1], df['Close'].iloc[-2]
        vol_curr, vol_prev = df['Volume'].iloc[-1], df['Volume'].iloc[-2]
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("현재가", f"{int(curr):,}원", f"{int(curr-prev):,} ({((curr-prev)/prev)*100:.2f}%)")
        c2.metric("거래량", f"{int(vol_curr):,}", f"{((vol_curr-vol_prev)/vol_prev)*100:+.1f}% 전일비")
        c3.metric("고가", f"{int(df['High'].iloc[-1]):,}원")
        c4.metric("저가", f"{int(df['Low'].iloc[-1]):,}원")
        st.write("---")

    # 차트
    for i in [5, 20, 40, 60]: df[f'MA{i}'] = df['Close'].rolling(window=i).mean()
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']), row=1, col=1)
    for ma in [5, 20, 40, 60]: fig.add_trace(go.Scatter(x=df.index, y=df[f'MA{ma}'], name=f'MA{ma}'), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['Volume']), row=2, col=1)
    fig.update_layout(xaxis_rangeslider_visible=False, height=500, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

if __name__ == '__main__':
    main()