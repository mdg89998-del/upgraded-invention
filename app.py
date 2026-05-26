import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 앱 시작 시 딱 한 번만 종목 리스트 확보 (실패 시 대체 리스트 활용)
@st.cache_data
def get_stock_data():
    try:
        # FinanceDataReader의 내장 데이터셋을 활용해 서버 호출 부하 최소화
        df = fdr.StockListing('KRX')[['Code', 'Name']]
    except:
        # 서버 장애 시 대비한 광범위한 하드코딩 리스트 (일부 대표 종목)
        data = {
            'Code': ['005930', '000660', '035420', '005380', '068270', '034220', '005490', '000270', '066570', '005380'],
            'Name': ['삼성전자', 'SK하이닉스', 'NAVER', '현대차', '셀트리온', 'LG디스플레이', 'POSCO홀딩스', '기아', 'LG전자', '현대차']
        }
        df = pd.DataFrame(data)
    return df

def main():
    st.set_page_config(page_title="AI PRO ANALYZER", layout="wide")
    stock_df = get_stock_data()

    # 2. 검색 인터페이스
    st.sidebar.subheader("🔍 종목 검색")
    query = st.sidebar.text_input("종목명 입력 (예: 삼성, 카카오)")
    
    # 검색어에 따른 필터링 (완전 일치 또는 포함되는 모든 것)
    if query:
        filtered_df = stock_df[stock_df['Name'].str.contains(query, na=False)]
    else:
        filtered_df = stock_df

    # 3. 검색 결과 선택 (필터링된 리스트 활용)
    selected_name = st.sidebar.selectbox("종목 선택", filtered_df['Name'].unique())
    interval = st.sidebar.radio("차트 주기", ["일봉", "주봉", "월봉"], horizontal=True)

    # 4. 데이터 로드 (코드 추출)
    target_code = stock_df[stock_df['Name'] == selected_name]['Code'].values[0]
    
    # 차트 데이터 로드 (에러 방지)
    try:
        df = fdr.DataReader(target_code, '2023-01-01')
        if interval == '주봉': df = df.resample('W').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
        elif interval == '월봉': df = df.resample('ME').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
        df = df.dropna()
    except:
        st.error("데이터 서버 연결 문제로 해당 종목의 차트를 불러올 수 없습니다.")
        return

    # 5. 분석 로직 (복합 매매 알고리즘)
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    val = (100 - (100 / (1 + (gain / loss)))).iloc[-1]
    
    golden = (df['MA5'].iloc[-2] < df['MA20'].iloc[-2]) and (df['MA5'].iloc[-1] > df['MA20'].iloc[-1])

    # 6. UI 구성
    st.title(f"📈 {selected_name} ({interval})")
    
    # 매매 시그널 변수 고정 (에러 방지)
    signal, color, desc = "관망", "gray", "특별한 신호가 없습니다."
    if golden and val < 70: signal, color, desc = "강력 매수", "green", "골든크로스 발생! 상승 추세입니다."
    elif val > 75: signal, color, desc = "매도", "red", "과열 상태입니다."
    elif golden: signal, color, desc = "매수", "blue", "골든크로스 발생!"
    elif val < 30: signal, color, desc = "저점 매수", "orange", "과매도 구간입니다."

    st.markdown(f"### 🎯 시그널: <span style='color:{color}'>{signal}</span>", unsafe_allow_html=True)
    st.info(f"진단: {desc} (현재 RSI: {val:.1f})")

    # 차트
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['Volume']), row=2, col=1)
    fig.update_layout(height=500, template="plotly_white", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

if __name__ == '__main__':
    main()