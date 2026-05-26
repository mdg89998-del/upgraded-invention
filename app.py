import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# 1. 데이터 로드 (캐시 사용으로 데이터가 한 번 들어오면 고정됨)
@st.cache_data(ttl=86400)
def get_stock_data():
    try:
        # 데이터가 서버에서 오든 안 오든, 한 번 성공하면 캐시됨
        df = fdr.StockListing('KRX')[['Code', 'Name']]
    except:
        # 비상용 리스트 (서버 죽었을 때 대비)
        df = pd.DataFrame({'Code': ['005930', '000660', '035420', '005380', '068270'], 
                           'Name': ['삼성전자', 'SK하이닉스', 'NAVER', '현대차', '셀트리온']})
    return df

def main():
    st.set_page_config(page_title="AI PRO ANALYZER", layout="wide")
    
    # 캐시된 데이터를 무조건 먼저 불러옴
    stock_df = get_stock_data()

    st.sidebar.subheader("🔍 종목 검색")
    query = st.sidebar.text_input("종목명 입력")
    
    # 필터링 로직 (데이터가 로드된 후 실행되도록 보장)
    filtered_df = stock_df[stock_df['Name'].str.contains(query, na=False)] if query else stock_df
    
    # 선택 박스
    selected_name = st.sidebar.selectbox("종목 선택", filtered_df['Name'].tolist())
    interval = st.sidebar.radio("차트 주기", ["일봉", "주봉", "월봉"], horizontal=True)

    # 차트 데이터 로드
    target_code = stock_df[stock_df['Name'] == selected_name]['Code'].values[0]
    
    try:
        df = fdr.DataReader(target_code, '2023-01-01')
        if interval == '주봉': df = df.resample('W').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
        elif interval == '월봉': df = df.resample('ME').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
        df = df.dropna()
    except:
        st.error("데이터 로드 중 오류 발생")
        return

    # 지표 계산 (안정적 RSI)
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rsi_val = (100 - (100 / (1 + (gain / loss)))).iloc[-1]
    
    # 출력값 예외 방지 (None이나 NaN 일 경우 강제 치환)
    rsi = rsi_val if not np.isnan(rsi_val) else 50.0
    
    # 시그널 로직
    golden = (df['MA5'].iloc[-2] < df['MA20'].iloc[-2]) and (df['MA5'].iloc[-1] > df['MA20'].iloc[-1])
    signal, color = ("골든크로스 매수", "green") if golden else ("관망", "gray")

    st.title(f"📈 {selected_name} ({interval})")
    st.markdown(f"### 🎯 시그널: <span style='color:{color}'>{signal}</span>", unsafe_allow_html=True)
    st.info(f"RSI 지표: {rsi:.1f}")

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['Volume']), row=2, col=1)
    fig.update_layout(height=500, template="plotly_white", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

if __name__ == '__main__':
    main()