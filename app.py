import streamlit as st
import pandas as pd
from datetime import datetime
from urllib.parse import quote
import xml.etree.ElementTree as ET
import requests

st.set_page_config(page_title="태형레이더", page_icon="📡", layout="wide")

st.title("📡 태형레이더")
st.caption("4대 지수 자동 조회 + 구도식 관심도 레이더")

try:
    import yfinance as yf
    YF_OK = True
except Exception:
    YF_OK = False

# ======================
# 4대 지수
# ======================

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

def calc_index_rows():
    rows = []
    for item in INDEXES:
        live = fetch_index(item["티커"])
        if live:
            rows.append({**item, **live, "신호": signal_text(live["등락률"])})
        else:
            rows.append({
                **item,
                "현재값": None,
                "전일종가": None,
                "등락률": 0.0,
                "상태": "데이터 대기",
                "신호": "데이터 대기",
            })
    df = pd.DataFrame(rows)
    df["TAO 추정 기여"] = df["등락률"] * df["가중치"]
    return df

# ======================
# 관심도 레이더
# ======================

KEYWORDS = [
    {"키워드": "SK하이닉스 HBM", "테마": "AI/HBM", "구도관점": "LONG 핵심 후보"},
    {"키워드": "삼성전자 HBM", "테마": "AI/HBM", "구도관점": "KOSPI 핵심 영향"},
    {"키워드": "한미반도체 HBM", "테마": "HBM 장비", "구도관점": "장비 밸류체인"},
    {"키워드": "엔비디아 AI", "테마": "Global AI", "구도관점": "미국 AI 선행 신호"},
    {"키워드": "TSMC AI", "테마": "Taiwan AI", "구도관점": "대만 반도체 핵심"},
    {"키워드": "마이크론 HBM", "테마": "Memory", "구도관점": "메모리 업황 선행"},
    {"키워드": "브로드컴 AI", "테마": "Global AI", "구도관점": "AI 네트워크/ASIC"},
    {"키워드": "반도체 장비", "테마": "Semi Equipment", "구도관점": "장비 투자심리"},
    {"키워드": "AI 반도체", "테마": "AI/Semi", "구도관점": "전체 테마 온도"},
    {"키워드": "전력기기 AI 데이터센터", "테마": "전력/인프라", "구도관점": "AI 인프라 확산"},
    {"키워드": "로봇 휴머노이드", "테마": "Robot", "구도관점": "차세대 성장 테마"},
    {"키워드": "방산 수출", "테마": "Defense", "구도관점": "이벤트/수주 모멘텀"},
]

GOOD_WORDS = ["수주", "계약", "증설", "공급", "상향", "흑자", "호실적", "AI", "HBM", "데이터센터", "수출", "신고가"]
BAD_WORDS = ["소송", "적자", "하향", "감산", "규제", "압수수색", "유증", "전환사채", "상폐", "급락"]

@st.cache_data(ttl=300)
def fetch_naver_news_rss(keyword):
    # 네이버 뉴스 검색 RSS는 공식 API가 아니라 공개 RSS 성격이라 환경에 따라 막힐 수 있음
    try:
        url = f"https://newssearch.naver.com/search.naver?where=rss&query={quote(keyword)}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=6)
        if res.status_code != 200:
            return None

        root = ET.fromstring(res.content)
        items = root.findall(".//item")
        news = []
        for item in items[:20]:
            title = item.findtext("title") or ""
            desc = item.findtext("description") or ""
            link = item.findtext("link") or ""
            pub = item.findtext("pubDate") or ""
            text = (title + " " + desc)
            news.append({
                "title": title.replace("<b>", "").replace("</b>", ""),
                "description": desc.replace("<b>", "").replace("</b>", ""),
                "link": link,
                "pubDate": pub,
                "text": text,
            })
        return news
    except Exception:
        return None

def keyword_score(keyword, news):
    if news is None:
        return 0, 0, 0, "데이터 대기"

    count = len(news)
    text = " ".join([n["text"] for n in news])
    good = sum(text.count(w) for w in GOOD_WORDS)
    bad = sum(text.count(w) for w in BAD_WORDS)

    base = min(55, count * 3)
    sentiment = min(25, good * 3) - min(20, bad * 4)
    theme_bonus = 15 if any(x in keyword for x in ["HBM", "AI", "반도체", "TSMC", "엔비디아"]) else 5

    score = int(max(0, min(100, base + sentiment + theme_bonus)))

    if score >= 80:
        stage = "관심 급증"
    elif score >= 65:
        stage = "관심 상승"
    elif score >= 45:
        stage = "관찰"
    else:
        stage = "약함"

    return score, good, bad, stage

def calc_attention_rows():
    rows = []
    sample_titles = {}
    for k in KEYWORDS:
        news = fetch_naver_news_rss(k["키워드"])
        score, good, bad, stage = keyword_score(k["키워드"], news)
        count = 0 if news is None else len(news)
        rows.append({
            **k,
            "뉴스수": count,
            "긍정키워드": good,
            "부정키워드": bad,
            "관심도점수": score,
            "단계": stage,
            "상태": "자동" if news is not None else "데이터 대기",
        })
        sample_titles[k["키워드"]] = [] if news is None else [n["title"] for n in news[:3]]
    return pd.DataFrame(rows).sort_values("관심도점수", ascending=False), sample_titles

# ======================
# UI
# ======================

if st.button("🔄 전체 새로고침"):
    st.cache_data.clear()
    st.rerun()

index_df = calc_index_rows()
total = index_df["TAO 추정 기여"].sum()

tab1, tab2, tab3 = st.tabs(["🌏 글로벌 지수", "🔍 관심도 레이더", "🧠 TAO 시그널"])

with tab1:
    st.subheader("4대 지수 자동 조회")

    cols = st.columns(4)
    for i, r in index_df.iterrows():
        with cols[i]:
            value = "-" if pd.isna(r["현재값"]) else f"{r['현재값']:,.2f}"
            delta = "데이터 대기" if r["상태"] != "자동" else f"{r['등락률']:+.2f}%"
            st.metric(f"{r['지역']} · {r['지수']}", value, delta)
            st.caption(f"{r['신호']} · {r['메모']}")

    show = index_df.copy()
    show["현재값"] = show["현재값"].apply(lambda x: "-" if pd.isna(x) else f"{x:,.2f}")
    show["전일종가"] = show["전일종가"].apply(lambda x: "-" if pd.isna(x) else f"{x:,.2f}")
    show["등락률"] = show["등락률"].apply(lambda x: f"{x:+.2f}%")
    show["가중치"] = show["가중치"].apply(lambda x: f"{x*100:.0f}%")
    show["TAO 추정 기여"] = show["TAO 추정 기여"].apply(lambda x: f"{x:+.2f}%p")
    st.dataframe(show, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("구도식 관심도 레이더")
    st.caption("네이버 뉴스 RSS를 자동 수집해 키워드별 관심도 점수를 계산합니다.")

    att_df, titles = calc_attention_rows()

    top = att_df.head(4)
    cols = st.columns(4)
    for i, r in top.reset_index(drop=True).iterrows():
        with cols[i]:
            st.metric(f"{r['키워드']}", f"{r['관심도점수']}점", r["단계"])
            st.caption(f"{r['테마']} · {r['구도관점']}")

    st.divider()

    display = att_df.copy()
    st.dataframe(display, use_container_width=True, hide_index=True)

    st.subheader("상위 키워드 뉴스 샘플")
    for _, r in att_df.head(5).iterrows():
        with st.expander(f"{r['키워드']} · {r['관심도점수']}점"):
            ts = titles.get(r["키워드"], [])
            if ts:
                for t in ts:
                    st.write("• " + t)
            else:
                st.write("뉴스 데이터를 가져오지 못했습니다.")

with tab3:
    st.subheader("TAO 종합 시그널")

    att_df, _ = calc_attention_rows()
    attention_score = float(att_df["관심도점수"].head(5).mean()) if len(att_df) else 0
    market_component = 50 + total * 10
    gudo_signal = int(max(0, min(100, attention_score * 0.65 + market_component * 0.35)))

    c1, c2, c3 = st.columns(3)
    c1.metric("4대 지수 기반 영향", f"{total:+.2f}%")
    c2.metric("관심도 평균", f"{attention_score:.0f}점")
    c3.metric("TAO 종합 시그널", f"{gudo_signal}점")

    if gudo_signal >= 80:
        st.success("구도 스타일 관점에서 시장 관심과 지수 환경이 모두 강한 구간입니다.")
    elif gudo_signal >= 65:
        st.info("구도 스타일 관점에서 관심도가 살아있는 구간입니다.")
    elif gudo_signal >= 45:
        st.warning("관심도는 있으나 방향성 확인이 필요한 구간입니다.")
    else:
        st.error("관심도와 시장 환경이 모두 약한 구간입니다.")

    st.subheader("구도 후보 상위")
    candidate = att_df[["키워드", "테마", "구도관점", "관심도점수", "단계"]].head(8)
    st.dataframe(candidate, use_container_width=True, hide_index=True)

st.caption("주의: 관심도 레이더는 매수/매도 신호가 아니라 구도 스타일 후보를 찾기 위한 조사 시작 신호입니다.")
