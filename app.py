import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# 데이터 캐싱 (절대 삭제 금지)
@st.cache_data(ttl=86400)
def get_stock_data():
    try:
        # KRX 전체 종목 데이터 가져오기
        df = fdr.StockListing('KRX')[['Code', 'Name']]
    except:
        df = pd.DataFrame({'Code': ['005930'], 'Name': ['삼성전자']})
    return df

def main():
    st.set_page_config(page_title="AI PRO ANALYZER", layout="wide")
    stock_df = get_stock_data()

    # 1. 검색창 (사이드바)
    st.sidebar.subheader("🔍 종목 검색")
    query = st.sidebar.text_input("종목명 입력")
    
    # 필터링
    filtered_df = stock_df[stock_df['Name'].str.contains(query, na=False)] if query else stock_df
    
    # 2. 선택창
    selected_name = st.sidebar.selectbox("종목 선택", filtered_df['Name'].tolist())
    interval = st.sidebar.radio("차트 주기", ["일봉", "주봉", "월봉"], horizontal=True)
    
    # 3. 매핑 핵심: 선택된 이름으로 정확한 코드 찾기
    # .loc를 사용하여 데이터가 존재할 때만 코드를 추출
    match = stock_df[stock_df['Name'] == selected_name]
    if not match.empty:
        target_code = match['Code'].iloc[0]
        
        # 4. 차트 데이터 로드
        try:
            df = fdr.DataReader(target_code, '2023-01-01')
            if interval == '주봉': df = df.resample('W').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
            elif interval == '월봉': df = df.resample('ME').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
            df = df.dropna()
        except:
            st.error("차트 데이터를 불러오는 중 오류가 발생했습니다.")
            return

        # 5. UI 출력
        st.title(f"📈 {selected_name} ({interval})")
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']), row=1, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df['Volume']), row=2, col=1)
        fig.update_layout(height=500, template="plotly_white", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("선택하신 종목의 코드를 찾을 수 없습니다.")

if __name__ == '__main__':
    main()