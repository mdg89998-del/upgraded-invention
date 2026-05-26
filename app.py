import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 데이터 로드 및 주기 변환 (안전 처리)
@st.cache_data
def get_data(code, interval):
    df = fdr.DataReader(code, '2020-01-01') # 충분한 데이터를 위해 기간 확장
    if df.empty: return df
    
    if interval == '주봉':
        df = df.resample('W').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
    elif interval == '월봉':
        df = df.resample('ME').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
    
    # 비어있는 행 제거
    df = df.dropna()
    return df

def main():
    st.set_page_config(page_title="AI PRO CHART", layout="wide")
    stock_list = fdr.StockListing('KRX')[['Code', 'Name']]

    with st.sidebar:
        query = st.text_input("종목 검색")
        filtered = stock_list[stock_list['Name'].str.contains(query, na=False)] if query else stock_list
        selected = st.selectbox("검색 결과", filtered['Name'], key="selector")
        interval = st.radio("차트 주기", ["일봉", "주봉", "월봉"], horizontal=True)
        submit = st.button("분석 실행")

    code = stock_list[stock_list['Name'] == selected]['Code'].values[0]
    df = get_data(code, interval)

    if df.empty:
        st.error("해당 기간의 데이터를 불러올 수 없습니다.")
        return

    st.title(f"📈 {selected} ({interval})")

    # 이평선 추가 (5, 20, 40, 60)
    for i in [5, 20, 40, 60]: df[f'MA{i}'] = df['Close'].rolling(window=i).mean()

    # 2. 전문 캔들차트 구현
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
    
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='시세'), row=1, col=1)
    
    # 이평선
    for ma in [5, 20, 40, 60]:
        fig.add_trace(go.Scatter(x=df.index, y=df[f'MA{ma}'], name=f'MA{ma}', line=dict(width=1.5)), row=1, col=1)
        
    # 거래량
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='거래량', marker_color='gray'), row=2, col=1)

    fig.update_layout(xaxis_rangeslider_visible=False, height=600, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

if __name__ == '__main__':
    main()