import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 안정적인 데이터 로드 (서버 장애 시 내장 데이터 사용)
@st.cache_data(ttl=86400)
def get_stock_data():
    try:
        # FinanceDataReader 기본 KRX 데이터 가져오기
        df = fdr.StockListing('KRX')[['Code', 'Name']]
    except:
        # 실패 시 예비 데이터
        df = pd.DataFrame({'Code': ['005930', '000660', '035420', '005380', '068270'], 
                           'Name': ['삼성전자', 'SK하이닉스', 'NAVER', '현대차', '셀트리온']})
    return df

def main():
    st.set_page_config(page_title="AI PRO ANALYZER", layout="wide")
    stock_df = get_stock_data()

    # 2. 사이드바 검색
    st.sidebar.subheader("🔍 종목 검색")
    query = st.sidebar.text_input("종목명 입력 (예: 카카오, 기아)")
    
    # 검색어 필터링
    if query:
        filtered_df = stock_df[stock_df['Name'].str.contains(query, na=False)]
    else:
        filtered_df = stock_df
    
    # 검색 결과가 하나라도 있을 때만 처리
    if not filtered_df.empty:
        selected_name = st.sidebar.selectbox("종목 선택", filtered_df['Name'].tolist())
        interval = st.sidebar.radio("차트 주기", ["일봉", "주봉", "월봉"], horizontal=True)
        
        # 3. 데이터 로드 및 검증
        target_code = stock_df[stock_df['Name'] == selected_name]['Code'].values[0]
        
        try:
            df = fdr.DataReader(target_code, '2023-01-01')
            if interval == '주봉': df = df.resample('W').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
            elif interval == '월봉': df = df.resample('ME').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
            df = df.dropna()
        except:
            st.error("해당 종목의 데이터를 불러올 수 없습니다.")
            return

        # 4. 분석 로직
        df['MA5'] = df['Close'].rolling(5).mean()
        df['MA20'] = df['Close'].rolling(20).mean()
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi = (100 - (100 / (1 + (gain / loss)))).iloc[-1]
        golden = (df['MA5'].iloc[-2] < df['MA20'].iloc[-2]) and (df['MA5'].iloc[-1] > df['MA20'].iloc[-1])

        # 5. UI 출력 (에러 방지: 변수 미리 선언)
        signal, color, desc = "관망", "gray", "특별한 신호가 없습니다."
        if golden and rsi < 70: signal, color, desc = "강력 매수", "green", "골든크로스 발생!"
        elif rsi > 75: signal, color, desc = "매도", "red", "과열 상태입니다."
        elif golden: signal, color, desc = "매수", "blue", "골든크로스 발생!"
        elif rsi < 30: signal, color, desc = "저점 매수", "orange", "과매도 구간입니다."

        st.title(f"📈 {selected_name} ({interval})")
        st.markdown(f"### 🎯 시그널: <span style='color:{color}'>{signal}</span>", unsafe_allow_html=True)
        st.info(f"진단: {desc} (RSI: {rsi:.1f})")

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']), row=1, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df['Volume']), row=2, col=1)
        fig.update_layout(height=500, template="plotly_white", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("검색 결과가 없습니다.")

if __name__ == '__main__':
    main()