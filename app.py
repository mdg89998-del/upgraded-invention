import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 서버 접속을 최소화하고, 실패 시에도 작동하는 강력한 데이터 로드
@st.cache_data(ttl=86400)
def get_stock_data():
    try:
        # 실제 데이터 호출
        df = fdr.StockListing('KRX')[['Code', 'Name']]
    except:
        # 접속 실패 시, 주요 종목을 포함한 기본 데이터 제공
        df = pd.DataFrame({
            'Code': ['005930', '000660', '035420', '005380', '068270', '034220', '005490', '000270'], 
            'Name': ['삼성전자', 'SK하이닉스', 'NAVER', '현대차', '셀트리온', 'LG디스플레이', 'POSCO홀딩스', '기아']
        })
    return df

def main():
    st.set_page_config(page_title="AI PRO ANALYZER", layout="wide")
    stock_df = get_stock_data()

    # 2. 검색 최적화: 사이드바에서 선택한 종목을 세션으로 관리
    with st.sidebar:
        st.subheader("🔍 종목 찾기")
        query = st.text_input("종목명 입력")
        
        # 필터링: 검색어가 있을 때만 해당 항목 보여줌
        search_list = stock_df['Name'].tolist()
        if query:
            filtered = [n for n in search_list if query in n]
            options = filtered if filtered else search_list
        else:
            options = search_list
            
        selected_name = st.selectbox("검색 결과", options)
        interval = st.radio("차트 주기", ["일봉", "주봉", "월봉"], horizontal=True)

    # 3. 안전한 매핑 (에러 방지: 이름으로 코드 찾기)
    try:
        target_code = stock_df.loc[stock_df['Name'] == selected_name, 'Code'].values[0]
        df = fdr.DataReader(target_code, '2020-01-01')
        
        # 주기 처리
        if interval == '주봉':
            df = df.resample('W').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
        elif interval == '월봉':
            df = df.resample('ME').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
        df = df.dropna()
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return

    # 4. 분석 (이평선 + RSI + 골든크로스)
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    val = (100 - (100 / (1 + (gain / loss)))).iloc[-1]
    
    golden = (df['MA5'].iloc[-2] < df['MA20'].iloc[-2]) and (df['MA5'].iloc[-1] > df['MA20'].iloc[-1])

    # 5. UI 출력
    st.title(f"📈 {selected_name} ({interval})")
    
    # 변수 초기화 (에러 방지용)
    signal, color, desc = "관망", "gray", "특별한 신호가 없습니다."
    if golden and val < 70: signal, color, desc = "강력 매수", "green", "골든크로스 발생! 상승 추세입니다."
    elif val > 75: signal, color, desc = "매도", "red", "과열 상태입니다. 차익 실현 고려하세요."
    elif golden: signal, color, desc = "매수", "blue", "골든크로스 발생했으나 과열 주의하세요."
    elif val < 30: signal, color, desc = "저점 매수", "orange", "과매도 구간 반등을 노리세요."

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("현재가", f"{int(df['Close'].iloc[-1]):,}원")
    c2.metric("거래량", f"{int(df['Volume'].iloc[-1]):,}")
    c3.metric("고가", f"{int(df['High'].iloc[-1]):,}원")
    c4.metric("저가", f"{int(df['Low'].iloc[-1]):,}원")
    
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