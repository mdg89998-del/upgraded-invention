import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 서버 접속 오류 방지용 안전 데이터 로드
@st.cache_data(ttl=86400) # 하루에 한 번만 로드하여 속도 최적화
def get_stock_data():
    try:
        # KRX 리스트 로드 시도
        df = fdr.StockListing('KRX')[['Code', 'Name']]
    except:
        # 실패 시 최소한의 기본 리스트 유지
        df = pd.DataFrame({'Code': ['005930', '000660', '035420', '005380'], 
                           'Name': ['삼성전자', 'SK하이닉스', 'NAVER', '현대차']})
    return df

def main():
    st.set_page_config(page_title="AI PRO ANALYZER", layout="wide")
    stock_df = get_stock_data()
    
    # 2. 검색창 구성
    with st.sidebar:
        st.subheader("🔍 종목 찾기")
        query = st.text_input("종목명 입력")
        
        # 검색어 필터링
        if query:
            filtered_df = stock_df[stock_df['Name'].str.contains(query, na=False)]
        else:
            filtered_df = stock_df
            
        selected_name = st.selectbox("검색 결과", filtered_df['Name'])
        interval = st.radio("차트 주기", ["일봉", "주봉", "월봉"], horizontal=True)

    # 3. 차트 및 분석 (안전하게 실행)
    target_code = stock_df[stock_df['Name'] == selected_name]['Code'].values[0]
    
    # 데이터 로드 (실패 시 에러 처리)
    try:
        df = fdr.DataReader(target_code, '2020-01-01')
        if interval == '주봉':
            df = df.resample('W').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
        elif interval == '월봉':
            df = df.resample('ME').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
        df = df.dropna()
    except:
        st.error("데이터를 가져오는 중 오류가 발생했습니다. 잠시 후 다시 시도하세요.")
        return

    st.title(f"📈 {selected_name} ({interval})")

    # 정보창
    if len(df) >= 2:
        curr, prev = df['Close'].iloc[-1], df['Close'].iloc[-2]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("현재가", f"{int(curr):,}원", f"{int(curr-prev):,} ({((curr-prev)/prev)*100:.2f}%)")
        c2.metric("거래량", f"{int(df['Volume'].iloc[-1]):,}")
        c3.metric("고가", f"{int(df['High'].iloc[-1]):,}원")
        c4.metric("저가", f"{int(df['Low'].iloc[-1]):,}원")
        
        # AI 알고리즘 진단
        delta = df['Close'].diff()
        rsi = 100 - (100 / (1 + (delta.where(delta > 0, 0).rolling(14).mean() / (-delta.where(delta < 0, 0).rolling(14).mean()))))
        val = rsi.iloc[-1]
        st.subheader("🤖 AI 알고리즘 진단")
        st.write(f"현재 RSI: **{val:.2f}** | 진단: **{'매수' if val < 40 else '관망' if val < 60 else '매도'}** 구간")
        st.write("---")

    # 차트
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['Volume']), row=2, col=1)
    fig.update_layout(height=500, template="plotly_white", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

if __name__ == '__main__':
    main()