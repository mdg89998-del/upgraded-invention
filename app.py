import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 데이터 로드 (서버 접속 실패 대비 강화)
@st.cache_data(ttl=3600)
def get_stock_data():
    try:
        df = fdr.StockListing('KRX')[['Code', 'Name']]
    except:
        # 서버 접속 실패 시 안전을 위해 기본 리스트 생성
        df = pd.DataFrame({'Code': ['005930', '000660', '035420'], 
                           'Name': ['삼성전자', 'SK하이닉스', 'NAVER']})
    
    name_to_code = dict(zip(df['Name'], df['Code']))
    return df, name_to_code

def main():
    st.set_page_config(page_title="AI PRO ANALYZER", layout="wide")
    
    # 서버 에러 발생해도 앱은 실행되도록 구성
    try:
        stock_df, name_to_code = get_stock_data()
    except Exception as e:
        st.error(f"서버 연결 오류: {e}")
        return

    # 2. 사이드바 구성
    with st.sidebar:
        st.subheader("🔍 종목 찾기")
        query = st.text_input("종목명 검색")
        
        filtered_names = [name for name in name_to_code.keys() if query in name] if query else list(name_to_code.keys())
        selected = st.selectbox("검색 결과", filtered_names)
        interval = st.radio("차트 주기", ["일봉", "주봉", "월봉"], horizontal=True)

    # 3. 데이터 로드 (주기에 따른 처리)
    target_code = name_to_code.get(selected, '005930')
    df = fdr.DataReader(target_code, '2020-01-01')
    
    if interval == '주봉':
        df = df.resample('W').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
    elif interval == '월봉':
        df = df.resample('ME').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
    df = df.dropna()

    st.title(f"📈 {selected} ({interval})")

    # 4. 요약 정보창 & AI 진단 (오류 방지)
    if len(df) >= 14:
        curr = df['Close'].iloc[-1]
        prev = df['Close'].iloc[-2]
        
        # 상세 정보
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("현재가", f"{int(curr):,}원", f"{int(curr-prev):,} ({((curr-prev)/prev)*100:.2f}%)")
        c2.metric("거래량", f"{int(df['Volume'].iloc[-1]):,}")
        c3.metric("고가", f"{int(df['High'].iloc[-1]):,}원")
        c4.metric("저가", f"{int(df['Low'].iloc[-1]):,}원")
        
        # AI 알고리즘 매매 추종 (RSI 계산)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi = 100 - (100 / (1 + (gain / loss)))
        curr_rsi = rsi.iloc[-1]
        
        st.subheader("🤖 AI 알고리즘 실시간 진단")
        if curr_rsi < 20: st.error(f"1단계 (강력 매수) - RSI: {curr_rsi:.2f}")
        elif curr_rsi < 40: st.warning(f"2단계 (매수) - RSI: {curr_rsi:.2f}")
        elif curr_rsi < 60: st.info(f"3단계 (관망) - RSI: {curr_rsi:.2f}")
        elif curr_rsi < 80: st.warning(f"4단계 (매도) - RSI: {curr_rsi:.2f}")
        else: st.error(f"5단계 (강력 매도) - RSI: {curr_rsi:.2f}")
        
        st.write("---")

    # 5. 차트
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['Volume']), row=2, col=1)
    fig.update_layout(height=500, template="plotly_white", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

if __name__ == '__main__':
    main()