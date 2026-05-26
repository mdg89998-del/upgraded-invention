import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 종목 리스트를 앱 실행 시 딱 한 번만 불러와서 저장
@st.cache_data(ttl=86400)
def load_all_stocks():
    try:
        # 전체 종목을 가져옴
        df = fdr.StockListing('KRX')[['Code', 'Name']]
        return df
    except:
        # 서버 장애 시 기본값
        return pd.DataFrame({'Code': ['005930', '000660', '035420', '005380', '068270'], 
                           'Name': ['삼성전자', 'SK하이닉스', 'NAVER', '현대차', '셀트리온']})

def main():
    st.set_page_config(page_title="AI PRO ANALYZER", layout="wide")
    
    # 캐시된 전체 종목 리스트 불러오기
    stock_df = load_all_stocks()

    # 2. 사이드바 검색
    with st.sidebar:
        st.subheader("🔍 종목 찾기")
        query = st.text_input("종목명 입력 (예: 삼성, 카카오)")
        
        # 검색어 기반 필터링
        if query:
            filtered_df = stock_df[stock_df['Name'].str.contains(query, na=False)]
        else:
            filtered_df = stock_df
            
        # 검색 결과가 없으면 전체 리스트 보여줌
        search_results = filtered_df['Name'].tolist() if not filtered_df.empty else stock_df['Name'].tolist()
        selected = st.selectbox("검색 결과", search_results)
        interval = st.radio("차트 주기", ["일봉", "주봉", "월봉"], horizontal=True)

    # 3. 데이터 로드
    target_code = stock_df[stock_df['Name'] == selected]['Code'].values[0]
    
    try:
        df = fdr.DataReader(target_code, '2020-01-01')
        if interval == '주봉': df = df.resample('W').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
        elif interval == '월봉': df = df.resample('ME').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
        df = df.dropna()
    except:
        st.error("데이터 로드 실패")
        return

    # 4. 분석 및 출력 (로직 유지)
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rsi = 100 - (100 / (1 + (gain / loss)))
    val = rsi.iloc[-1]
    
    golden = (df['MA5'].iloc[-2] < df['MA20'].iloc[-2]) and (df['MA5'].iloc[-1] > df['MA20'].iloc[-1])
    signal, color, desc = "관망", "gray", "특별한 신호가 없습니다."
    if golden and val < 70: signal, color, desc = "강력 매수", "green", "골든크로스 발생! 상승 추세입니다."
    elif val > 75: signal, color, desc = "매도", "red", "과열 상태입니다. 차익 실현 고려하세요."
    elif golden: signal, color, desc = "매수", "blue", "골든크로스 발생했으나 과열 주의하세요."
    elif val < 30: signal, color, desc = "저점 매수", "orange", "과매도 구간 반등을 노리세요."

    st.title(f"📈 {selected} ({interval})")
    
    c1, c2, c3, c4 = st.columns(4)
    curr, prev = df['Close'].iloc[-1], df['Close'].iloc[-2]
    c1.metric("현재가", f"{int(curr):,}원", f"{int(curr-prev):,} ({(curr-prev)/prev*100:.2f}%)")
    c2.metric("거래량", f"{int(df['Volume'].iloc[-1]):,}", f"{((df['Volume'].iloc[-1]-df['Volume'].iloc[-2])/df['Volume'].iloc[-2])*100:+.1f}% 전일비")
    c3.metric("고가", f"{int(df['High'].iloc[-1]):,}원")
    c4.metric("저가", f"{int(df['Low'].iloc[-1]):,}원")
    
    st.subheader("🤖 AI 알고리즘 복합 진단")
    st.markdown(f"### 🎯 시그널: <span style='color:{color}'>{signal}</span>", unsafe_allow_html=True)
    st.info(f"분석: {desc} (RSI: {val:.1f})")

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], name='MA5'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='MA20'), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['Volume']), row=2, col=1)
    fig.update_layout(height=500, template="plotly_white", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

if __name__ == '__main__':
    main()