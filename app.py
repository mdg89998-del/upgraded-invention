import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 강력한 방어형 데이터 로드
@st.cache_data(ttl=86400)
def get_stock_data():
    # 서버 오류가 발생해도 절대 멈추지 않도록 구성
    try:
        # 1순위: KRX 데이터 시도
        df = fdr.StockListing('KRX')[['Code', 'Name']]
    except:
        # 2순위: 실패 시 즉시 로컬 데이터로 대체
        df = pd.DataFrame({
            'Code': ['005930', '000660', '035420', '005380', '068270', '034220', '005490'], 
            'Name': ['삼성전자', 'SK하이닉스', 'NAVER', '현대차', '셀트리온', 'LG디스플레이', 'POSCO홀딩스']
        })
    return df

def main():
    st.set_page_config(page_title="AI PRO ANALYZER", layout="wide")
    
    # 데이터 로드
    stock_df = get_stock_data()

    # 2. 사이드바 검색 (데이터프레임 필터링)
    with st.sidebar:
        st.subheader("🔍 종목 찾기")
        query = st.text_input("종목명 입력")
        
        # 검색 필터링: 검색어가 있으면 필터링, 없으면 전체
        if query:
            filtered_df = stock_df[stock_df['Name'].str.contains(query, na=False)]
        else:
            filtered_df = stock_df
            
        # 검색 결과가 하나라도 있으면 선택, 없으면 경고 후 기본 리스트 표시
        if not filtered_df.empty:
            options = filtered_df['Name'].tolist()
        else:
            options = stock_df['Name'].tolist()
            
        selected_name = st.selectbox("검색 결과", options)
        interval = st.radio("차트 주기", ["일봉", "주봉", "월봉"], horizontal=True)

    # 3. 데이터 로드 및 차트 처리
    try:
        target_code = stock_df[stock_df['Name'] == selected_name]['Code'].values[0]
        df = fdr.DataReader(target_code, '2020-01-01')
        
        # 주기 처리
        if interval == '주봉':
            df = df.resample('W').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
        elif interval == '월봉':
            df = df.resample('ME').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
        df = df.dropna()
    except:
        st.error("종목 데이터를 가져오는 중 오류 발생. 잠시 후 다시 시도하세요.")
        return

    # 4. 분석 지표 계산
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    
    # RSI 계산 (에러 방지)
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    val = (100 - (100 / (1 + (gain / loss)))).iloc[-1]
    
    # 5. UI 출력
    st.title(f"📈 {selected_name} ({interval})")
    
    # 지표 및 차트
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['Volume']), row=2, col=1)
    fig.update_layout(height=500, template="plotly_white", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

if __name__ == '__main__':
    main()