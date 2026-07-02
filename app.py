import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="태형레이더", page_icon="📡", layout="wide")

st.title("📡 태형레이더 v1.2")
st.caption("한국·미국·일본·대만 증시 실시간 연결 1차 버전")

st.divider()

# yfinance는 무료 공개 데이터라 지연/누락이 있을 수 있습니다.
try:
    import yfinance as yf
    YFINANCE_OK = True
except Exception:
    YFINANCE_OK = False

MARKETS = [
    {"지역": "한국", "이름": "KOSPI", "티커": "^KS11", "설명": "TAO 직접 영향 가능성 높음"},
    {"지역": "한국", "이름": "KOSDAQ", "티커": "^KQ11", "설명": "중소형 성장주/벤처 심리 확인"},
    {"지역": "미국", "이름": "NASDAQ", "티커": "^IXIC", "설명": "AI·반도체 선행 신호"},
    {"지역": "미국", "이름": "SOX 반도체", "티커": "^SOX", "설명": "SK하이닉스·삼성전자 영향 추정 핵심"},
    {"지역": "일본", "이름": "Nikkei 225", "티커": "^N225", "설명": "글로벌 위험선호·반도체 장비주 심리"},
    {"지역": "일본", "이름": "TOPIX", "티커": "1306.T", "설명": "일본 전체 증시 방향 확인"},
    {"지역": "대만", "이름": "TAIEX", "티커": "^TWII", "설명": "TSMC·AI 반도체 밸류체인 핵심"},
    {"지역": "대만", "이름": "TSMC", "티커": "2330.TW", "설명": "글로벌 AI/HBM 투자심리 핵심"},
]

@st.cache_data(ttl=300)
def get_market_data(ticker):
    if not YFINANCE_OK:
        return None

    try:
        data = yf.download(ticker, period="5d", interval="1d", progress=False, auto_adjust=False)
        if data is None or data.empty:
            return None

        close = data["Close"].dropna()
        if len(close) < 2:
            return None

        last = float(close.iloc[-1])
        prev = float(close.iloc[-2])
        change_pct = (last / prev - 1) * 100

        return {
            "현재값": last,
            "전일대비": change_pct,
        }
    except Exception:
        return None

def score_from_change(change_pct):
    if change_pct is None:
        return 50
    # 상승/하락 자체보다 "시장 충격/관심도" 관점. 절대 변동이 클수록 점수 상승.
    abs_move = abs(change_pct)
    score = 50 + min(45, abs_move * 12)
    return int(min(100, max(0, score)))

def signal_text(change_pct):
    if change_pct is None:
        return "데이터 확인 필요"
    if change_pct >= 2:
        return "강한 상승"
    if change_pct >= 0.5:
        return "상승"
    if change_pct > -0.5:
        return "보합"
    if change_pct > -2:
        return "하락"
    return "강한 하락"

rows = []
for m in MARKETS:
    live = get_market_data(m["티커"])
    if live:
        change_pct = live["전일대비"]
        current = live["현재값"]
        source = "live"
    else:
        change_pct = None
        current = None
        source = "fallback"

    rows.append({
        **m,
        "현재값": current,
        "등락률": change_pct,
        "시장점수": score_from_change(change_pct),
        "신호": signal_text(change_pct),
        "데이터": source,
    })

df = pd.DataFrame(rows)

st.header("🌏 글로벌 시장 레이더")

cols = st.columns(4)
for i, row in df.iterrows():
    with cols[i % 4]:
        value = f"{row['시장점수']}점"
        delta = None if pd.isna(row["등락률"]) else f"{row['등락률']:+.2f}%"
        st.metric(
            label=f"{row['지역']} · {row['이름']}",
            value=value,
            delta=delta
        )
        st.caption(f"{row['신호']} · {row['설명']}")

st.divider()

st.header("📊 시장 영향도 요약")
view = df.copy()
view["현재값"] = view["현재값"].apply(lambda x: "-" if pd.isna(x) else f"{x:,.2f}")
view["등락률"] = view["등락률"].apply(lambda x: "-" if pd.isna(x) else f"{x:+.2f}%")
st.dataframe(view, use_container_width=True, hide_index=True)

st.divider()

st.header("🧠 TAO 영향도 초안")

# 아직 실제 구도 포지션을 모르므로 시장 기반 임시 영향도
weights = {
    "SOX 반도체": 0.25,
    "NASDAQ": 0.18,
    "TAIEX": 0.16,
    "TSMC": 0.16,
    "KOSPI": 0.15,
    "Nikkei 225": 0.06,
    "KOSDAQ": 0.03,
    "TOPIX": 0.01,
}

impact_rows = []
estimated_impact = 0

for _, r in df.iterrows():
    w = weights.get(r["이름"], 0)
    chg = 0 if pd.isna(r["등락률"]) else r["등락률"]
    impact = chg * w
    estimated_impact += impact
    impact_rows.append({
        "요인": r["이름"],
        "등락률": "-" if pd.isna(r["등락률"]) else f"{r['등락률']:+.2f}%",
        "가중치": f"{w*100:.0f}%",
        "TAO 추정 기여": f"{impact:+.2f}%p",
    })

impact_df = pd.DataFrame(impact_rows)

c1, c2, c3 = st.columns(3)
c1.metric("시장 기반 TAO 추정 영향", f"{estimated_impact:+.2f}%")
c2.metric("데이터 업데이트", datetime.now().strftime("%H:%M"))
c3.metric("모델 단계", "v1.2")

st.dataframe(impact_df, use_container_width=True, hide_index=True)

st.info("주의: 이 값은 실제 TAO 포지션이 아니라, 글로벌 반도체/AI 시장 움직임을 기준으로 만든 임시 추정치입니다. 다음 버전에서 기준가·순자산·주식편입비를 입력해 보정합니다.")

st.divider()

st.header("🚀 다음 업그레이드")
st.write("v1.3 : TAO 기준가, 설정원본액, 순자산, 주식편입비 입력")
st.write("v1.4 : 6/23 이후 기준가 그래프")
st.write("v2.0 : 실제 기준가와 예상치 비교")
st.write("v3.0 : 구도 AI 모델")
