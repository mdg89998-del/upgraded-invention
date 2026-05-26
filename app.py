import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 데이터 로드 (에러 방지)
@st.cache_data(ttl=600)
def get_data(code, interval):
    try:
        df = fdr.DataReader(code, '2020-01-01')
        if interval == '주봉':
            df = df.resample('W').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
        elif interval == '월봉':
            df = df.resample('ME').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
        return df.dropna()
    except:
        return pd.DataFrame()

def main():
    st.set_page_config(page_title="AI PRO", layout="wide")
    
    # 종목 리스트
    try: stock_list = fdr.StockListing('KRX')[['Code', 'Name']]
    except: stock_list = pd.DataFrame({'Code': ['005930'], 'Name': ['삼성전자']})

    # 사이드바
    with st.sidebar:
        query = st.text_input("종목 검색")
        filtered = stock_list[stock_list['Name'].str.contains(query, na=False)] if query else stock_list
        selected = st.selectbox("검색 결과", filtered['Name'], key="stock_sel")
        interval = st.radio("차트 주기", ["일봉", "주봉", "월봉"], horizontal=True)

    # 데이터 가져오기
    code = stock_list[stock_list['Name'] == selected]['Code'].values[0]
    df = get_data(code, interval)

    st.title(f"📈 {selected} ({interval})")

    # 정보창 (데이터가 충분할 때만 표시)
    if not df.empty and len(df) >= 2:
        curr = df['Close'].iloc[-1]
        prev = df['Close'].iloc[-2]
        vol_curr = df['Volume'].iloc[-1]
        vol_prev = df['Volume'].iloc[-2]
        
        diff = curr - prev
        rate = (diff / prev) * 100
        vol_rate = ((vol_curr - vol_prev) / vol_prev) * 100
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("현재가", f"{int(curr):,}원", f"{int(diff):,} ({rate:.2f}%)")
        c2.metric("거래량", f"{int(vol_curr):,}", f"{vol_rate:+.1f}% 전일비")
        c3.metric("고가", f"{int(df['High'].iloc[-1]):,}원")
        c4.metric("저가", f"{int(df['Low'].iloc[-1]):,}원")
        st.write("---")

    # 차트 (데이터가 있을 때만 생성)
    if not df.empty:
        for i in [5, 20, 40, 60]: df[f'MA{i}'] = df['Close'].rolling(window=i).mean()
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='시세'), row=1, col=1)
        for ma in [5, 20, 40, 60]: fig.add_trace(go.Scatter(x=df.index, y=df[f'MA{ma}'], name=f'MA{ma}'), row=1, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='거래량'), row=2, col=1)
        
        fig.update_layout(xaxis_rangeslider_visible=False, height=500, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("데이터를 불러올 수 없습니다. 종목을 다시 확인해주세요.")

if __name__ == '__main__':
    main()