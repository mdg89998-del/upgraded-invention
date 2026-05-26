import streamlit as st
import pandas as pd
import pandas_ta_classic as ta
import FinanceDataReader as fdr
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 캐싱된 리스트 로드
@st.cache_data
def get_stock_list():
    try: return fdr.StockListing('KRX')[['Code', 'Name']]
    except: return pd.DataFrame({'Code': ['005930'], 'Name': ['삼성전자']})

# 전체 구조를 함수화하여 UI 요소가 중복 생성되는 것 방지
def main():
    st.set_page_config(page_title="AI PRO", layout="wide")
    stock_list = get_stock_list()

    # 2. 사이드바
    with st.sidebar:
        st.title("🔍 종목 찾기")
        query = st.text_input("종목명 입력")
        
        # 검색 리스트 생성
        filtered = stock_list[stock_list['Name'].str.contains(query, na=False)] if query else stock_list
        selected = st.selectbox("검색 결과", filtered['Name'], key="stock_selector")
        
        submit = st.button("분석 실행")

    # 3. 메인 분석 (사이드바 버튼과 무관하게 선택된 종목으로 자동 업데이트)
    st.title(f"📈 {selected} 분석")
    
    code = stock_list[stock_list['Name'] == selected]['Code'].values[0]
    df = fdr.DataReader(code, '2022-01-01')

    # 지표 계산
    for i in [5, 20, 60, 120]: df[f'MA{i}'] = ta.ema(df['Close'], length=i)
    
    # 차트
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['Volume']), row=2, col=1)
    st.plotly_chart(fig, use_container_width=True)

if __name__ == '__main__':
    main()