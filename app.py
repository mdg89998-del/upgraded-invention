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
    main()