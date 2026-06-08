
import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np


# -----------------------------
# 종목 데이터 불러오기
# -----------------------------
@st.cache_data(ttl=86400)
def get_stock_data():
    try:
        df = fdr.StockListing('KRX')[['Code', 'Name']]

        if df.empty:
            raise ValueError("종목 데이터 없음")

        df['Code'] = df['Code'].astype(str)

    except Exception:
        df = pd.DataFrame({
            'Code': ['005930'],
            'Name': ['삼성전자']
        })

    return df


# -----------------------------
# RSI 계산 함수
# -----------------------------
def calculate_rsi(close, period=14):
    delta = close.diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


# -----------------------------
# 메인
# -----------------------------
def main():
    st.set_page_config(
        page_title="AI PRO ANALYZER",
        layout="wide"
    )

    stock_df = get_stock_data()

    st.sidebar.subheader("🔍 종목 검색")

    # 검색창
    query = st.sidebar.text_input(
        "종목명 또는 종목코드 입력",
        placeholder="예: 삼성, SK, 005930"
    )

    # 검색 로직 개선
    if query:
        filtered_df = stock_df[
            stock_df['Name'].str.contains(
                query,
                case=False,
                na=False
            )
            |
            stock_df['Code'].str.contains(
                query,
                na=False
            )
        ].copy()
    else:
        filtered_df = stock_df.copy()

    # 최대 100개 제한
    filtered_df = filtered_df.head(100)

    if filtered_df.empty:
        st.warning("검색된 종목이 없습니다.")
        st.stop()

    # 표시용 이름 생성
    filtered_df["display"] = (
        filtered_df["Name"]
        + " ("
        + filtered_df["Code"]
        + ")"
    )

    # 종목 선택
    selected_display = st.sidebar.selectbox(
        "종목 선택",
        filtered_df["display"].tolist()
    )

    # 선택값 찾기
    selected_row = filtered_df[
        filtered_df["display"] == selected_display
    ].iloc[0]

    selected_name = selected_row["Name"]
    target_code = selected_row["Code"]

    # 차트 주기
    interval = st.sidebar.radio(
        "차트 주기",
        ["일봉", "주봉", "월봉"],
        horizontal=True
    )

    # 데이터 불러오기
    try:
        df = fdr.DataReader(
            target_code,
            '2023-01-01'
        )

        if interval == '주봉':
            df = df.resample('W').agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            })

        elif interval == '월봉':
            df = df.resample('M').agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            })

        df.dropna(inplace=True)

    except Exception as e:
        st.error(f"데이터 로딩 오류: {e}")
        return

    # 데이터 부족 체크
    if len(df) < 20:
        st.warning("데이터가 부족합니다.")
        return

    # -----------------------------
    # 지표 계산
    # -----------------------------
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA20'] = df['Close'].rolling(20).mean()

    df['RSI'] = calculate_rsi(df['Close'])

    rsi = (
        df['RSI'].iloc[-1]
        if not np.isnan(df['RSI'].iloc[-1])
        else 50.0
    )

    # 현재 데이터
    curr = df['Close'].iloc[-1]
    prev = df['Close'].iloc[-2]

    vol_curr = df['Volume'].iloc[-1]
    vol_prev = df['Volume'].iloc[-2]

    # 증감률 계산
    price_diff = (
        ((curr - prev) / prev) * 100
        if prev != 0
        else 0
    )

    vol_diff = (
        ((vol_curr - vol_prev) / vol_prev) * 100
        if vol_prev != 0
        else 0
    )

    # -----------------------------
    # 화면 UI
    # -----------------------------
    st.title(
        f"📈 {selected_name} ({target_code})"
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "현재가",
        f"{int(curr):,}원",
        f"{price_diff:+.2f}%"
    )

    c2.metric(
        "거래량",
        f"{int(vol_curr):,}",
        f"{vol_diff:+.1f}%"
    )

    c3.metric(
        "시가",
        f"{int(df['Open'].iloc[-1]):,}원"
    )

    c4.metric(
        "고가",
        f"{int(df['High'].iloc[-1]):,}원"
    )

    # -----------------------------
    # AI 신호
    # -----------------------------
    golden = (
        df['MA5'].iloc[-2]
        < df['MA20'].iloc[-2]
    ) and (
        df['MA5'].iloc[-1]
        > df['MA20'].iloc[-1]
    )

    signal = "관망"
    color = "gray"
    desc = "특별한 신호가 없습니다."

    if golden and rsi < 70:
        signal = "강력 매수"
        color = "green"
        desc = "골든크로스 발생! 상승 추세입니다."

    elif rsi > 75:
        signal = "매도"
        color = "red"
        desc = "과열 상태입니다."

    elif golden:
        signal = "매수"
        color = "blue"
        desc = "골든크로스 발생."

    elif rsi < 30:
        signal = "저점 매수"
        color = "orange"
        desc = "과매도 구간입니다."

    st.markdown(
        f"""
        ### 🎯 AI 알고리즘 복합 진단:
        <span style='color:{color}'>
        {signal}
        </span>
        """,
        unsafe_allow_html=True
    )

    st.info(
        f"{desc} (RSI: {rsi:.1f})"
    )

    # -----------------------------
    # 차트
    # -----------------------------
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.7, 0.3]
    )

    # 캔들
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name="캔들"
        ),
        row=1,
        col=1
    )

    # 이동평균선
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['MA5'],
            mode='lines',
            name='MA5'
        ),
        row=1,
        col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['MA20'],
            mode='lines',
            name='MA20'
        ),
        row=1,
        col=1
    )

    # 거래량
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df['Volume'],
            name="거래량"
        ),
        row=2,
        col=1
    )

    fig.update_layout(
        height=700,
        template="plotly_white",
        xaxis_rangeslider_visible=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


if __name__ == '__main__':
    main()
```
