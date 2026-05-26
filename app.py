import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

@st.cache_data(ttl=86400)
def get_stock_data():
    try:
        # 데이터 호출 (실패 시 빈 데이터프레임 방지)
        df = fdr.StockListing('KRX')[['Code', 'Name']]
    except:
        df = pd.DataFrame({'Code': ['005930'], 'Name': ['삼성전자']})
    return df

def main():
    st.set_page_config(page_title="AI PRO ANALYZER", layout="wide")
    stock_df = get_stock_data()

    st.sidebar.subheader("🔍 종목 검색")
    query = st.sidebar.text_input("종목명 입력")
    
    # 검색 로직: 데이터가 비어있지 않은지 먼저 확인
    if not stock_df.empty:
        filtered_df = stock_df[stock_df['Name'].str.contains(query, na=False)] if query else stock_df
        
        # 검색 결과가 하나라도 있을 때만 처리
        if not filtered_df.empty:
            selected_name = st.sidebar.selectbox("종목 선택", filtered_df['Name'].tolist())
            interval = st.sidebar.radio("차트 주기", ["일봉", "주봉", "월봉"], horizontal=True)
            
            # 여기서 Index 에러가 나지 않도록 종목 코드 매핑 확인
            target_code = stock_df.loc[stock_df['Name'] == selected_name, 'Code'].iloc[0]
            
            try:
                df = fdr.DataReader(target_code, '2023-01-01')
                if interval == '주봉': df = df.resample('W').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
                elif interval == '월봉': df = df.resample('ME').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
                df = df.dropna()
            except:
                st.error("데이터를 가져오는 중 오류 발생")
                return

            # 분석 로직 (NaN 값 방지)
            df['MA5'] = df['Close'].rolling(5).mean()
            df['MA20'] = df['Close'].rolling(20).mean()
            delta = df['Close'].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rsi_val = (100 - (100 / (1 + (gain / loss)))).iloc[-1]
            rsi = rsi_val if not np.isnan(rsi_val) else 50.0

            # UI 출력
            st.title(f"📈 {selected_name}")
            st.info(f"현재 RSI: {rsi:.1f}")
            
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']), row=1, col=1)
            fig.add_trace(go.Bar(x=df.index, y=df['Volume']), row=2, col=1)
            fig.update_layout(height=500, template="plotly_white", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("검색된 종목이 없습니다.")
    else:
        st.error("종목 데이터를 불러오지 못했습니다.")

if __name__ == '__main__':
    main()# [추가] 1. 상세 지표 계산 및 전일 대비 로직
        curr = df['Close'].iloc[-1]
        prev = df['Close'].iloc[-2]
        vol_curr = df['Volume'].iloc[-1]
        vol_prev = df['Volume'].iloc[-2]
        
        price_diff = ((curr - prev) / prev) * 100
        vol_diff = ((vol_curr - vol_prev) / vol_prev) * 100
        
        # [추가] 2. 상세 정보 출력 (4개 컬럼)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("현재가", f"{int(curr):,}원", f"{price_diff:+.2f}%")
        c2.metric("거래량", f"{int(vol_curr):,}", f"{vol_diff:+.1f}% 전일비")
        c3.metric("시가", f"{int(df['Open'].iloc[-1]):,}원")
        c4.metric("고가", f"{int(df['High'].iloc[-1]):,}원")

        # [추가] 3. 분석 로직 (골든크로스 & RSI 복합 필터링)
        golden = (df['MA5'].iloc[-2] < df['MA20'].iloc[-2]) and (df['MA5'].iloc[-1] > df['MA20'].iloc[-1])
        
        signal, color, desc = "관망", "gray", "특별한 신호가 없습니다."
        if golden and rsi < 70: 
            signal, color, desc = "강력 매수", "green", "골든크로스 발생! 상승 추세입니다."
        elif rsi > 75: 
            signal, color, desc = "매도", "red", "과열 상태입니다. 차익 실현 고려하세요."
        elif golden: 
            signal, color, desc = "매수", "blue", "골든크로스 발생했으나 과열 주의하세요."
        elif rsi < 30: 
            signal, color, desc = "저점 매수", "orange", "과매도 구간입니다. 반등을 노리세요."

        # [추가] 4. 결과 출력
        st.markdown(f"### 🎯 시그널: <span style='color:{color}'>{signal}</span>", unsafe_allow_html=True)
        st.info(f"AI 복합 진단: {desc} (RSI: {rsi:.1f})")