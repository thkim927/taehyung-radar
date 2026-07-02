import streamlit as st
import pandas as pd
from datetime import datetime
from urllib.parse import quote
import xml.etree.ElementTree as ET
import requests

st.set_page_config(page_title="태형레이더", page_icon="📡", layout="wide")

st.title("📡 태형레이더")
st.caption("4대 지수 자동 조회 + 네이버/구글 뉴스 관심도 레이더")

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

KEYWORDS = [
    {"네이버": "SK하이닉스 HBM", "구글": "SK hynix HBM", "표시명": "SK하이닉스 HBM", "테마": "AI/HBM", "구도관점": "LONG 핵심 후보"},
    {"네이버": "삼성전자 HBM", "구글": "Samsung Electronics HBM", "표시명": "삼성전자 HBM", "테마": "AI/HBM", "구도관점": "KOSPI 핵심 영향"},
    {"네이버": "한미반도체 HBM", "구글": "Hanmi Semiconductor HBM", "표시명": "한미반도체 HBM", "테마": "HBM 장비", "구도관점": "장비 밸류체인"},
    {"네이버": "엔비디아 AI", "구글": "Nvidia AI", "표시명": "엔비디아 AI", "테마": "Global AI", "구도관점": "미국 AI 선행 신호"},
    {"네이버": "TSMC AI", "구글": "TSMC AI semiconductor", "표시명": "TSMC AI", "테마": "Taiwan AI", "구도관점": "대만 반도체 핵심"},
    {"네이버": "마이크론 HBM", "구글": "Micron HBM memory", "표시명": "마이크론 HBM", "테마": "Memory", "구도관점": "메모리 업황 선행"},
    {"네이버": "브로드컴 AI", "구글": "Broadcom AI chip", "표시명": "브로드컴 AI", "테마": "Global AI", "구도관점": "AI 네트워크/ASIC"},
    {"네이버": "AI 반도체", "구글": "AI semiconductor", "표시명": "AI 반도체", "테마": "AI/Semi", "구도관점": "전체 테마 온도"},
    {"네이버": "AI 데이터센터 전력기기", "구글": "data center power equipment AI", "표시명": "AI 데이터센터 전력기기", "테마": "전력/인프라", "구도관점": "AI 인프라 확산"},
    {"네이버": "휴머노이드 로봇", "구글": "humanoid robot", "표시명": "휴머노이드 로봇", "테마": "Robot", "구도관점": "차세대 성장 테마"},
    {"네이버": "방산 수출", "구글": "K defense export", "표시명": "방산 수출", "테마": "Defense", "구도관점": "수주/이벤트 모멘텀"},
]

GOOD_WORDS_KR = ["수주", "계약", "증설", "공급", "상향", "흑자", "호실적", "AI", "HBM", "데이터센터", "수출", "신고가", "급등"]
BAD_WORDS_KR = ["소송", "적자", "하향", "감산", "규제", "압수수색", "유증", "전환사채", "상폐", "급락"]

GOOD_WORDS_EN = ["surge", "rally", "record", "beat", "upgrade", "growth", "AI", "HBM", "supply", "contract", "data center", "demand"]
BAD_WORDS_EN = ["lawsuit", "miss", "downgrade", "fall", "drop", "plunge", "risk", "cut", "delay", "weak"]

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
        return {"현재값": last, "전일종가": prev_close, "등락률": change_pct, "상태": "자동"}
    except Exception:
        return None

@st.cache_data(ttl=300)
def fetch_google_news(keyword):
    try:
        url = f"https://news.google.com/rss/search?q={quote(keyword)}&hl=ko&gl=KR&ceid=KR:ko"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code != 200:
            return None
        root = ET.fromstring(res.content)
        items = root.findall(".//item")
        news = []
        for item in items[:20]:
            title = item.findtext("title") or ""
            link = item.findtext("link") or ""
            pub = item.findtext("pubDate") or ""
            news.append({"source": "Google", "title": title, "link": link, "pubDate": pub, "text": title})
        return news
    except Exception:
        return None

@st.cache_data(ttl=300)
def fetch_naver_news(keyword):
    try:
        url = f"https://newssearch.naver.com/search.naver?where=rss&query={quote(keyword)}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=8)
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
            clean_title = title.replace("<b>", "").replace("</b>", "")
            clean_desc = desc.replace("<b>", "").replace("</b>", "")
            news.append({"source": "Naver", "title": clean_title, "link": link, "pubDate": pub, "text": clean_title + " " + clean_desc})
        return news
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
            rows.append({**item, "현재값": None, "전일종가": None, "등락률": 0.0, "상태": "데이터 대기", "신호": "데이터 대기"})
    df = pd.DataFrame(rows)
    df["TAO 추정 기여"] = df["등락률"] * df["가중치"]
    return df

def score_keyword(naver_news, google_news):
    naver_count = 0 if naver_news is None else len(naver_news)
    google_count = 0 if google_news is None else len(google_news)
    combined = []
    if naver_news:
        combined.extend(naver_news)
    if google_news:
        combined.extend(google_news)
    if not combined:
        return 0, naver_count, google_count, 0, 0, "데이터 대기"

    text = " ".join([n["text"] for n in combined])
    text_lower = text.lower()

    good_kr = sum(text.count(w) for w in GOOD_WORDS_KR)
    bad_kr = sum(text.count(w) for w in BAD_WORDS_KR)
    good_en = sum(text_lower.count(w.lower()) for w in GOOD_WORDS_EN)
    bad_en = sum(text_lower.count(w.lower()) for w in BAD_WORDS_EN)

    good = good_kr + good_en
    bad = bad_kr + bad_en

    # 네이버와 구글을 둘 다 반영하되 중복 과열 방지
    count_score = min(55, naver_count * 2.3 + google_count * 2.1)
    sentiment = min(25, good * 3) - min(20, bad * 4)
    source_bonus = 10 if naver_count > 0 and google_count > 0 else 4
    score = int(max(0, min(100, count_score + sentiment + source_bonus)))

    if score >= 80:
        stage = "관심 급증"
    elif score >= 65:
        stage = "관심 상승"
    elif score >= 45:
        stage = "관찰"
    else:
        stage = "약함"

    return score, naver_count, google_count, good, bad, stage

def calc_attention_rows():
    rows = []
    titles = {}
    for k in KEYWORDS:
        naver = fetch_naver_news(k["네이버"])
        google = fetch_google_news(k["구글"])
        score, n_count, g_count, good, bad, stage = score_keyword(naver, google)

        sources = []
        if n_count > 0:
            sources.append("네이버")
        if g_count > 0:
            sources.append("구글")
        source_status = "+".join(sources) if sources else "데이터 대기"

        rows.append({
            **k,
            "네이버뉴스": n_count,
            "구글뉴스": g_count,
            "총뉴스": n_count + g_count,
            "긍정키워드": good,
            "부정키워드": bad,
            "관심도점수": score,
            "단계": stage,
            "상태": source_status,
        })

        sample = []
        if naver:
            sample.extend([f"[네이버] {n['title']}" for n in naver[:2]])
        if google:
            sample.extend([f"[구글] {n['title']}" for n in google[:2]])
        titles[k["표시명"]] = sample[:4]

    return pd.DataFrame(rows).sort_values("관심도점수", ascending=False), titles

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
    st.caption("네이버 뉴스 + 구글 뉴스 데이터를 동시에 수집해 관심도 점수를 계산합니다.")

    att_df, titles = calc_attention_rows()

    top = att_df.head(4)
    cols = st.columns(4)
    for i, r in top.reset_index(drop=True).iterrows():
        with cols[i]:
            st.metric(f"{r['표시명']}", f"{r['관심도점수']}점", r["단계"])
            st.caption(f"{r['테마']} · {r['상태']}")

    st.divider()
    st.dataframe(att_df, use_container_width=True, hide_index=True)

    st.subheader("상위 키워드 뉴스 샘플")
    for _, r in att_df.head(5).iterrows():
        with st.expander(f"{r['표시명']} · {r['관심도점수']}점 · {r['상태']}"):
            ts = titles.get(r["표시명"], [])
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
    candidate = att_df[["표시명", "테마", "구도관점", "네이버뉴스", "구글뉴스", "관심도점수", "단계", "상태"]].head(8)
    st.dataframe(candidate, use_container_width=True, hide_index=True)

st.caption("주의: 관심도 레이더는 매수/매도 신호가 아니라 구도 스타일 후보를 찾기 위한 조사 시작 신호입니다.")
