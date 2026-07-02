import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="태형레이더", page_icon="📡", layout="wide")

st.title("📡 태형레이더")
st.caption("NASDAQ · KOSPI · Nikkei 225 · TAIEX 자동 지수 레이더")

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

def calc_rows():
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
                "상태": "데이터 대기",
                "시장점수": 50,
                "신호": "데이터 대기",
            })
    return pd.DataFrame(rows)

if st.button("🔄 자동 새로고침"):
    st.cache_data.clear()
    st.rerun()

df = calc_rows()
df["TAO 추정 기여"] = df["등락률"] * df["가중치"]
total = df["TAO 추정 기여"].sum()

tab1, tab2, tab3 = st.tabs(["🌏 글로벌 지수", "🧠 TAO 영향", "🔍 관심도 레이더"])

with tab1:
    st.subheader("4대 지수 자동 조회")

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
    show["TAO 추정 기여"] = show["TAO 추정 기여"].apply(lambda x: f"{x:+.2f}%p")
    st.dataframe(show, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("시장 기반 TAO 예상 영향")

    c1, c2, c3 = st.columns(3)
    c1.metric("TAO 예상 영향", f"{total:+.2f}%")
    c2.metric("업데이트", datetime.now().strftime("%H:%M:%S"))
    c3.metric("자동 지수", "4개")

    impact = df[["지역", "지수", "등락률", "가중치", "TAO 추정 기여", "메모", "상태"]].copy()
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

with tab3:
    st.subheader("조회수/관심도 급증 레이더")
    st.caption("다음 업그레이드에서 구도식 관심도 포착 기능을 붙일 예정입니다.")

    concept = pd.DataFrame([
        {"항목": "네이버 뉴스 언급량", "상태": "예정", "설명": "종목명/테마 키워드 뉴스 증가율"},
        {"항목": "구글 트렌드", "상태": "예정", "설명": "검색 관심도 변화"},
        {"항목": "네이버 데이터랩", "상태": "예정", "설명": "국내 검색량 변화"},
        {"항목": "관심도 점수", "상태": "예정", "설명": "검색량+뉴스+시장방향 합산"},
    ])
    st.dataframe(concept, use_container_width=True, hide_index=True)

    st.info("목표: 조회수와 검색량이 갑자기 늘어나는 종목/테마를 잡아서 구도 스타일 후보로 표시합니다.")

st.caption("무료 공개 데이터 기반이라 지연·누락 가능성이 있습니다. 데이터 대기 상태가 나오면 새로고침해보세요.")
