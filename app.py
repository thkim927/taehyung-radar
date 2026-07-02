import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="태형레이더", page_icon="📡", layout="wide")

st.title("📡 태형레이더")
st.caption("NASDAQ · KOSPI · 일본 Nikkei · 대만 TAIEX 자동 지수 레이더")

try:
    import yfinance as yf
    YF_OK = True
except Exception:
    YF_OK = False

INDEXES = [
    {"지역": "미국", "지수": "NASDAQ", "티커": "^IXIC", "가중치": 0.35, "메모": "미국 AI·성장주 선행 신호"},
    {"지역": "한국", "지수": "KOSPI", "티커": "^KS11", "가중치": 0.35, "메모": "TAO 직접 영향 가능성"},
    {"지역": "일본", "지수": "Nikkei 225", "티커": "^N225", "가중치": 0.15, "메모": "아시아 위험선호"},
    {"지역": "대만", "지수": "TAIEX", "티커": "^TWII", "가중치": 0.15, "메모": "TSMC·AI 반도체 밸류체인"},
]

@st.cache_data(ttl=60)
def fetch_index(ticker):
    if not YF_OK:
        return None

    try:
        obj = yf.Ticker(ticker)

        # 장중 데이터 우선, 실패하면 일봉
        hist = obj.history(period="2d", interval="1m", prepost=True)
        if hist is None or hist.empty:
            hist = obj.history(period="5d", interval="1d")

        daily = obj.history(period="5d", interval="1d")

        if hist is None or hist.empty or daily is None or daily.empty:
            return None

        last = float(hist["Close"].dropna().iloc[-1])
        closes = daily["Close"].dropna()

        if len(closes) < 2:
            return None

        prev_close = float(closes.iloc[-2])
        change_pct = (last / prev_close - 1) * 100

        return {
            "현재값": last,
            "전일종가": prev_close,
            "등락률": change_pct,
            "상태": "자동",
        }
    except Exception:
        return None

def market_score(change):
    if change is None:
        return 50
    return int(max(0, min(100, 50 + abs(change) * 12)))

def signal_text(change):
    if change is None:
        return "데이터 대기"
    if change >= 2:
        return "강한 상승"
    if change >= 0.5:
        return "상승"
    if change > -0.5:
        return "보합"
    if change > -2:
        return "하락"
    return "강한 하락"

if st.button("🔄 지수 새로고침"):
    st.cache_data.clear()
    st.rerun()

rows = []
for item in INDEXES:
    live = fetch_index(item["티커"])
    if live:
        rows.append({**item, **live, "시장점수": market_score(live["등락률"]), "신호": signal_text(live["등락률"])})
    else:
        rows.append({
            **item,
            "현재값": None,
            "전일종가": None,
            "등락률": 0.0,
            "상태": "수동/대기",
            "시장점수": 50,
            "신호": "데이터 대기",
        })

df = pd.DataFrame(rows)

tab1, tab2, tab3 = st.tabs(["🌏 4대 지수", "✍️ 수동 보정", "🧠 TAO 영향"])

with tab1:
    st.subheader("자동 지수 레이더")

    cols = st.columns(4)
    for i, r in df.iterrows():
        with cols[i]:
            value = "-" if pd.isna(r["현재값"]) else f"{r['현재값']:,.2f}"
            delta = "데이터 대기" if r["상태"] != "자동" else f"{r['등락률']:+.2f}%"
            st.metric(f"{r['지역']} · {r['지수']}", value, delta)
            st.caption(f"{r['신호']} · {r['메모']}")

    st.divider()
    show = df.copy()
    show["현재값"] = show["현재값"].apply(lambda x: "-" if pd.isna(x) else f"{x:,.2f}")
    show["전일종가"] = show["전일종가"].apply(lambda x: "-" if pd.isna(x) else f"{x:,.2f}")
    show["등락률"] = show["등락률"].apply(lambda x: f"{x:+.2f}%")
    show["가중치"] = show["가중치"].apply(lambda x: f"{x*100:.0f}%")
    st.dataframe(show, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("수동 보정")
    st.caption("자동 조회가 실패하거나 숫자가 이상하면 등락률만 직접 수정하세요.")

    edited = st.data_editor(
        df[["지역", "지수", "티커", "등락률", "가중치", "메모", "상태"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "등락률": st.column_config.NumberColumn("등락률(%)", step=0.1, format="%.2f"),
            "가중치": st.column_config.NumberColumn("가중치", step=0.01, format="%.2f"),
        },
    )
    st.session_state["market_edited"] = edited

with tab3:
    st.subheader("시장 기반 TAO 예상 영향")

    calc = st.session_state.get("market_edited", df[["지역", "지수", "티커", "등락률", "가중치", "메모", "상태"]]).copy()
    calc["TAO 추정 기여"] = calc["등락률"] * calc["가중치"]
    total = calc["TAO 추정 기여"].sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("TAO 예상 영향", f"{total:+.2f}%")
    c2.metric("업데이트", datetime.now().strftime("%H:%M:%S"))
    c3.metric("지수 구성", "NASDAQ/KOSPI/Nikkei/TAIEX")

    impact = calc.copy()
    impact["등락률"] = impact["등락률"].apply(lambda x: f"{x:+.2f}%")
    impact["가중치"] = impact["가중치"].apply(lambda x: f"{x*100:.0f}%")
    impact["TAO 추정 기여"] = impact["TAO 추정 기여"].apply(lambda x: f"{x:+.2f}%p")
    st.dataframe(impact, use_container_width=True, hide_index=True)

    if total > 1:
        st.success("4대 지수 기준으로는 TAO에 긍정적 영향 가능성이 큽니다.")
    elif total < -1:
        st.error("4대 지수 기준으로는 TAO에 부정적 영향 가능성이 큽니다.")
    else:
        st.info("4대 지수 기준 TAO 영향은 제한적입니다.")

st.caption("무료 공개 데이터 기반이라 지연·누락 가능성이 있습니다. 자동 조회 실패 시 수동 보정 탭을 사용하세요.")
