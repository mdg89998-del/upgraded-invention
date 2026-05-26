import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# 1. 안전한 데이터 로딩 (로컬 파일 캐싱 활용)
@st.cache_data(ttl=86400)
def get_stock_data():
    csv_file = 'stock_list.csv'
    # 로컬에 파일이 있으면 무조건 그것을 읽음 (서버 접속 횟수 최소화)
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
    else:
        try:
            # 첫 실행 시에만 서버 접속 시도
            df = fdr.StockListing('KRX')[['Code', 'Name']]
            df.to_csv(csv_file, index=False)
        except:
            # 완전히 서버가 죽어있을 경우 대비한 기본 데이터
            df = pd.DataFrame({'Code': ['005930', '000660', '035420', '005380'], 
                               'Name': ['삼성전자', 'SK하이닉스', 'NAVER', '현대차']})
    return df

def main():
    st.set_page_config(page_title="AI PRO ANALYZER", layout="wide")
    stock_df = get_stock_data()

    # 2. 사이드바 검색 (데이터프레임 필터링 방식 최적화)
    with st.sidebar:
        st.subheader("🔍 종목 찾기")
        query = st.text_input("종목명 입력")
        
        # 검색 필터링
        filtered_df = stock_df[stock_df['Name'].str.contains(query, na=False)] if query else stock_df
        
        # 안전한 선택 리스트 생성
        options = filtered_df['Name'].tolist() if not filtered_df.empty else stock_df['Name'].tolist()
        selected_name = st.selectbox("검색 결과", options)
        interval = st.radio("차트 주기", ["일봉", "주봉", "월봉"], horizontal=True)

    # 3. 데이터 로드 (코드 매핑)
    target_code = stock_df[stock_df['Name'] == selected_name]['Code'].values[0]
    
    try:
        df = fdr.DataReader(target_code, '2020-01-01')
        if interval == '주봉': df = df.resample('W').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
        elif interval == '월봉': df = df.resample('ME').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'})
        df = df.dropna()
    except:
        st.error("데이터 서버 접속 실패. 잠시 후 시도하세요.")
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
    
    curr, prev = df['Close'].iloc[-1], df['Close'].iloc[-2]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("현재가", f"{int(curr):,}원", f"{int(curr-prev):,} ({(curr-prev)/prev*100:.2f}%)")
    c2.metric("거래량", f"{int(df['Volume'].iloc[-1]):,}", f"{((df['Volume'].iloc[-1]-df['Volume'].iloc[-2])/df['Volume'].iloc[-2])*100:+.1f}% 전일비")
    c3.metric("고가", f"{int(df['High'].iloc[-1]):,}원")
    c4.metric("저가", f"{int(df['Low'].iloc[-1]):,}원")
    
    st.subheader("🤖 AI 알고리즘 진단")
    if golden and val < 70: st.success("강력 매수: 골든크로스 발생 및 상승 추세")
    elif val > 75: st.error("매도: 과열 구간입니다.")
    elif golden: st.warning("매수: 골든크로스 발생!")
    elif val < 30: st.info("저점 매수: 과매도 구간입니다.")
    else: st.write("관망: 특별한 신호가 없습니다.")

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], name='MA5'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='MA20'), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['Volume']), row=2, col=1)
    fig.update_layout(height=500, template="plotly_white", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

if __name__ == '__main__':
    main()