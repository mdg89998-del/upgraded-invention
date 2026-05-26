# ... (앞부분 생략) ...
    st.title(f"📈 {selected} ({interval})")
    
    # 데이터 준비
    curr = df['Close'].iloc[-1]
    prev = df['Close'].iloc[-2]
    diff = curr - prev
    rate = (diff / prev) * 100
    high = df['High'].iloc[-1]
    low = df['Low'].iloc[-1]
    vol = df['Volume'].iloc[-1]
    
    # 1. 정보창 1행 (현재가, 전일대비, 거래량)
    c1, c2, c3 = st.columns(3)
    c1.metric("현재가", f"{int(curr):,}원", f"{int(diff):,} ({rate:.2f}%)")
    c2.metric("거래량", f"{int(vol):,}")
    c3.metric("전일 종가", f"{int(prev):,}원")
    
    # 2. 정보창 2행 (고가, 저가)
    c4, c5 = st.columns(2)
    c4.metric("당일 고가", f"{int(high):,}원")
    c5.metric("당일 저가", f"{int(low):,}원")
    
    st.write("---") # 차트와 구분선
    
    # 3. 차트 생성
    # ... (기존 차트 코드) ...