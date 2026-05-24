import pandas as pd
import pandas_ta_classic as ta
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="AI STOCK", layout="centered")
st.title("📱 AI 자산 전광판")
st.write("---")

watchlist = {
    "대한항공": "003490.KS", "동진쎄미켐": "005160.KQ", "두산에너빌리티": "034020.KS",
    "마이크로투나노": "424980.KQ", "삼성SDI": "006400.KS", "삼성전기": "009150.KS",
    "삼성전자": "005930.KS", "세미파이브": "490470.KQ", "신성이엔지": "011930.KS",
    "아이티센": "124500.KS", "원익IPS": "240810.KS", "원익QnC": "074600.KQ",
    "주성엔지니어링": "036930.KQ", "케이엔솔": "053080.KS", "켐트로닉스": "089010.KQ",
    "키움증권": "039490.KS", "필옵틱스": "161580.KQ", "현대차": "005380.KS",
    "LIG넥스원": "079550.KS", "HD현대일렉트릭": "043200.KS", "LG전자": "066570.KS",
    "SK하이닉스": "000660.KS", "SKC": "011790.KS", "델(DELL)": "DELL",
    "마이크론(MU)": "MU", "샌디스크(WDC)": "WDC", "써클(USDC)": "USDC-USD",
    "알파벳(GOOGL)": "GOOGL", "아이온큐(IONQ)": "IONQ", "AMD": "AMD",
    "인텔(INTC)": "INTC", "퀄컴(QCOM)": "QCOM", "테슬라(TSLA)": "TSLA",
    "비트코인(BTC)": "BTC-USD", "이더리움(ETH)": "ETH-USD"
}

with st.spinner("🔄 분석 중..."):
    for name, ticker in sorted(watchlist.items()):
        try:
            df = yf.Ticker(ticker).history(period="6mo")
            if df.empty or len(df) < 20: continue

            df["RSI"] = ta.rsi(df["Close"], length=14)
            df["E20"] = ta.ema(df["Close"], length=20)
            df["E60"] = ta.ema(df["Close"], length=60)
            df.dropna(subset=["RSI", "E20", "E60"], inplace=True)
            if df.empty: continue

            c_pr = df["Close"].iloc[-1]
            p_pr = df["Close"].iloc[-2]
            pct = ((c_pr - p_pr) / p_pr) * 100
            rsi = df["RSI"].iloc[-1]
            bull = bool(df["E20"].iloc[-1] > df["E60"].iloc[-1])

            p_fmt = f"${c_pr:,.1f}" if c_pr < 1000 else f"{int(c_pr):,}원"
            if "BTC" in ticker: p_fmt = f"${c_pr:,.0f}"

            sig = "🔥 강력매수" if rsi <= 30 else ("🟢 과매도" if rsi <= 35 else ("🔴 과매수" if rsi >= 70 else "🔵 관망"))
            trend = "📈 정배열" if bull else "📉 역배열"

            t_txt = f"{name} | {p_fmt} ({pct:+.1f}%) | {sig}"
            
            with st.expander(t_txt):
                st.write(f"🚦 AI 상태 진단: **{sig}** (RSI: {rsi:.1f})")
                st.write(f"📈 이동평균선 흐름: **{trend}**")
                
                c_df = df[['Close', 'E20', 'E60']].tail(60).copy()
                c_df.columns = ['Close', 'EMA20', 'EMA60']
                st.line_chart(c_df, use_container_width=True)
        except Exception:
            continue

st.success("✅ 완료! 종목 카드를 누르면 차트가 정상적으로 열립니다.")