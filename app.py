import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="태형레이더", page_icon="📡", layout="wide")

st.title("📡 태형레이더 US Live Test")
st.caption("미국장 실시간 테스트용 · 자동 수집 실패 시 수동 입력 가능")

try:
    import yfinance as yf
    YF_OK = True
except Exception:
    YF_OK = False

US_TICKERS = [
    {"factor": "NASDAQ", "ticker": "^IXIC", "weight": 0.16, "memo": "미국 성장주/AI 전반"},
    {"factor": "SOX 반도체", "ticker": "^SOX", "weight": 0.24, "memo": "반도체 섹터 핵심"},
    {"factor": "NVIDIA", "ticker": "NVDA", "weight": 0.12, "memo": "AI 사이클 선행"},
    {"factor": "AMD", "ticker": "AMD", "weight": 0.06, "memo": "AI GPU/반도체 심리"},
    {"factor": "Broadcom", "ticker": "AVGO", "weight": 0.08, "memo": "AI 네트워크/ASIC"},
    {"factor": "Micron", "ticker": "MU", "weight": 0.10, "memo": "메모리 업황 선행"},
    {"factor": "TSMC ADR", "ticker": "TSM", "weight": 0.10, "memo": "글로벌 파운드리/AI 밸류체인"},
]

ASIA_TICKERS = [
    {"factor": "KOSPI", "ticker": "^KS11", "weight": 0.08, "memo": "한국 대형주"},
    {"factor": "KOSDAQ", "ticker": "^KQ11", "weight": 0.02, "memo": "중소형 성장주"},
    {"factor": "Nikkei 225", "ticker": "^N225", "weight": 0.03, "memo": "일본 위험선호"},
    {"factor": "TAIEX", "ticker": "^TWII", "weight": 0.01, "memo": "대만 AI 밸류체인"},
]

ALL_TICKERS = US_TICKERS + ASIA_TICKERS

@st.cache_data(ttl=60)
def fetch_one(ticker):
    if not YF_OK:
        return None
    try:
        obj = yf.Ticker(ticker)

        # 장중 데이터 우선
        hist = obj.history(period="2d", interval="1m", prepost=True)
        if hist is None or hist.empty:
            hist = obj.history(period="5d", interval="1d")

        if hist is None or hist.empty:
            return None

        last = float(hist["Close"].dropna().iloc[-1])

        # 기준가: 전일 종가
        daily = obj.history(period="5d", interval="1d")
        if daily is None or daily.empty or len(daily["Close"].dropna()) < 2:
            return None

        closes = daily["Close"].dropna()
        prev_close = float(closes.iloc[-2])
        change_pct = (last / prev_close - 1) * 100

        return {
            "current": last,
            "change_pct": change_pct,
            "status": "자동",
        }
    except Exception:
        return None

def signal(change):
    if change is None:
        return "수동 필요"
    if change >= 3:
        return "강한 상승"
    if change >= 1:
        return "상승"
    if change > -1:
        return "보합"
    if change > -3:
        return "하락"
    return "강한 하락"

def score(change):
    if change is None:
        return 50
    return int(max(0, min(100, 50 + abs(change) * 12)))

if st.button("🔄 미국장 데이터 새로고침"):
    st.cache_data.clear()
    st.rerun()

rows = []
for item in ALL_TICKERS:
    live = fetch_one(item["ticker"])
    if live:
        chg = live["change_pct"]
        cur = live["current"]
        status = "자동"
    else:
        chg = 0.0
        cur = None
        status = "수동/대기"

    rows.append({
        "요인": item["factor"],
        "티커": item["ticker"],
        "현재값": cur,
        "등락률": chg,
        "가중치": item["weight"],
        "시장점수": score(chg),
        "신호": signal(chg),
        "메모": item["memo"],
        "상태": status,
    })

df = pd.DataFrame(rows)

tab1, tab2, tab3 = st.tabs(["🇺🇸 미국장 라이브", "✍️ 수동 보정", "🧠 TAO 영향"])

with tab1:
    st.subheader("미국장 핵심 지표")

    cols = st.columns(4)
    for i, r in df[df["요인"].isin([x["factor"] for x in US_TICKERS])].iterrows():
        with cols[i % 4]:
            delta = f"{r['등락률']:+.2f}%" if r["상태"] == "자동" else "데이터 대기"
            value = "-" if pd.isna(r["현재값"]) else f"{r['현재값']:,.2f}"
            st.metric(f"{r['요인']} ({r['티커']})", value, delta)
            st.caption(f"{r['신호']} · {r['메모']}")

    st.subheader("전체 데이터")
    show = df.copy()
    show["현재값"] = show["현재값"].apply(lambda x: "-" if pd.isna(x) else f"{x:,.2f}")
    show["등락률"] = show["등락률"].apply(lambda x: f"{x:+.2f}%")
    show["가중치"] = show["가중치"].apply(lambda x: f"{x*100:.0f}%")
    st.dataframe(show, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("자동 수집 실패 시 수동 보정")
    st.caption("등락률만 직접 고치면 TAO 영향도 계산에 바로 반영됩니다.")

    edited = st.data_editor(
        df[["요인", "티커", "등락률", "가중치", "메모", "상태"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "등락률": st.column_config.NumberColumn("등락률(%)", step=0.1, format="%.2f"),
            "가중치": st.column_config.NumberColumn("가중치", step=0.01, format="%.2f"),
        }
    )

    st.session_state["edited_market"] = edited

with tab3:
    st.subheader("TAO 시장 기반 예상 영향")

    calc_df = st.session_state.get("edited_market", df[["요인", "티커", "등락률", "가중치", "메모", "상태"]]).copy()
    calc_df["TAO 추정 기여"] = calc_df["등락률"] * calc_df["가중치"]
    total = calc_df["TAO 추정 기여"].sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("시장 기반 TAO 예상 영향", f"{total:+.2f}%")
    c2.metric("업데이트", datetime.now().strftime("%H:%M:%S"))
    c3.metric("모델", "US Live Test")

    top = calc_df.copy()
    top["절대기여"] = top["TAO 추정 기여"].abs()
    top = top.sort_values("절대기여", ascending=False)

    st.dataframe(
        top[["요인", "티커", "등락률", "가중치", "TAO 추정 기여", "메모", "상태"]],
        use_container_width=True,
        hide_index=True
    )

    if total > 1:
        st.success("현재 입력값 기준 TAO에 긍정적 영향 가능성이 큽니다.")
    elif total < -1:
        st.error("현재 입력값 기준 TAO에 부정적 영향 가능성이 큽니다.")
    else:
        st.info("현재 입력값 기준 TAO 영향은 제한적입니다.")

st.caption("주의: yfinance 무료 데이터는 지연·누락될 수 있습니다. 태형레이더는 자동+수동 백업 구조로 설계합니다.")
