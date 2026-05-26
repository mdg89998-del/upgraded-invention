import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 서버 장애를 대비한 하드코딩 리스트 (가장 안전)
@st.cache_data
def get_stock_data():
    # 실제 서버 접속
    try:
        df = fdr.StockListing('KRX')[['Code', 'Name']]
    except:
        # 서버 장애 시 사용할 안전한 기본 리스트
        df = pd.DataFrame({
            'Code': ['005930', '000660', '035420', '005380', '068270', '005490', '066570'], 
            'Name': ['삼성전자', 'SK하이닉스', 'NAVER', '현대차', '셀트리온', 'POSCO홀딩스', 'LG전자']
        })
    return df

def main():
    st.set_page_config(page_title="AI PRO ANALYZER", layout="wide")
    stock_df = get_stock_data()

    # 2. 사이드바 검색
    st.sidebar.subheader("🔍 종목 검색")
    query = st.sidebar.text_input("종목명 입력 (예: 삼성, 카카오)")
    
    # 검색 필터링
    filtered_df = stock_df[stock_df['Name'].str.contains(query, na=False)] if query else stock_df
    
    # 선택 박스 구성
    selected_name = st.sidebar.selectbox("종목 선택", filtered_df['Name'].tolist())
    interval = st.sidebar.radio("차트 주기", ["일봉", "주봉", "월봉"], horizontal=True)

    # 3. 데이터 로드 및 차트 처리 (에러 방어)
    try:
        target_code = stock_df.loc[stock_df['Name'] == selected_name, 'Code'].values[0]
        df = fdr.DataReader(target_code, '2023-01-01')
        
        if interval == '주봉': df = df.resample('W').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
        elif interval == '월봉': df = df.resample('ME').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
        df = df.dropna()
    except Exception as e:
        st.error("데이터 서버 연결 문제로 해당 종목을 불러올 수 없습니다.")
        return

    # 4. 분석 로직 (복합 매매 알고리즘)
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rsi = (100 - (100 / (1 + (gain / loss)))).iloc[-1]
    golden = (df['MA5'].iloc[-2] < df['MA20'].iloc[-2]) and (df['MA5'].iloc[-1] > df['MA20'].iloc[-1])

    # 5. UI 출력
    st.title(f"📈 {selected_name} ({interval})")
    
    # 시그널 변수 안전하게 초기화
    signal, color, desc = "관망", "gray", "특별한 신호가 없습니다."
    if golden and rsi < 70: signal, color, desc = "강력 매수", "green", "골든크로스 발생! 상승 추세입니다."
    elif rsi > 75: signal, color, desc = "매도", "red", "과열 상태입니다."
    elif golden: signal, color, desc = "매수", "blue", "골든크로스 발생!"
    elif rsi < 30: signal, color, desc = "저점 매수", "orange", "과매도 구간입니다."

    st.markdown(f"### 🎯 시그널: <span style='color:{color}'>{signal}</span>", unsafe_allow_html=True)
    st.info(f"진단: {desc} (현재 RSI: {rsi:.1f})")

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['Volume']), row=2, col=1)
    fig.update_layout(height=500, template="plotly_white", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

if __name__ == '__main__':
    main()