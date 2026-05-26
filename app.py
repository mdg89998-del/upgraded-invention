import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 안정적인 데이터 로드
@st.cache_data(ttl=86400)
def get_stock_list():
    try:
        df = fdr.StockListing('KRX')[['Code', 'Name']]
    except:
        df = pd.DataFrame({'Code': ['005930', '000660', '035420', '005380'], 
                           'Name': ['삼성전자', 'SK하이닉스', 'NAVER', '현대차']})
    return df

def main():
    st.set_page_config(page_title="AI PRO ANALYZER", layout="wide")
    stock_df = get_stock_list()
    name_to_code = dict(zip(stock_df['Name'], stock_df['Code']))

    with st.sidebar:
        st.subheader("🔍 종목 찾기")
        query = st.text_input("종목명 입력")
        filtered_names = [name for name in name_to_code.keys() if query in name] if query else list(name_to_code.keys())
        selected = st.selectbox("검색 결과", filtered_names)
        interval = st.radio("차트 주기", ["일봉", "주봉", "월봉"], horizontal=True)

    target_code = name_to_code.get(selected, '005930')
    df = fdr.DataReader(target_code, '2020-01-01')
    
    # 이동평균선 계산
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    
    # 2. AI 매매 로직 (골든크로스 + RSI)
    # 골든크로스 판단 (전일 MA5 < MA20 이었다가 오늘 MA5 > MA20인 경우)
    golden_cross = (df['MA5'].iloc[-2] < df['MA20'].iloc[-2]) and (df['MA5'].iloc[-1] > df['MA20'].iloc[-1])
    
    # RSI 계산
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rsi = 100 - (100 / (1 + (gain / loss)))
    val = rsi.iloc[-1]

    st.title(f"📈 {selected} ({interval})")

    # 3. AI 복합 분석
    st.subheader("🤖 AI 알고리즘 복합 진단")
    
    # 매매 판단 로직
    if golden_cross and val < 70:
        signal, color, desc = "강력 매수", "green", "골든크로스 발생! 상승 추세 전환이 강력합니다."
    elif val > 75:
        signal, color, desc = "매도", "red", "과열 상태입니다. 차익 실현을 고려하세요."
    elif golden_cross:
        signal, color, desc = "매수", "blue", "골든크로스가 발생했으나 과열을 주의하세요."
    elif val < 30:
        signal, color, desc = "저점 매수", "orange", "과매도 구간입니다. 반등을 노려볼 자리입니다."
    else:
        signal, color, desc = "관망", "gray", "특별한 신호가 없습니다. 추세를 지켜보세요."

    st.markdown(f"### 🎯 시그널: <span style='color:{color}'>{signal}</span>", unsafe_html=True)
    st.info(f"분석 내용: {desc} (현재 RSI: {val:.1f})")
    st.write("---")

    # 4. 차트 생성
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='시세'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], name='MA5', line=dict(color='orange')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='MA20', line=dict(color='blue')), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='거래량'), row=2, col=1)
    fig.update_layout(height=500, template="plotly_white", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

if __name__ == '__main__':
    main()