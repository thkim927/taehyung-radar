import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote
from datetime import datetime

st.set_page_config(page_title="태형레이더", page_icon="📡", layout="wide")

st.title("📡 태형레이더")
st.caption("4대 지수 자동 조회 + 뉴스 기반 자동 관심종목 TOP10 + 구도 후보 탭")

try:
    import yfinance as yf
    YF_OK = True
except Exception:
    YF_OK = False

# =========================
# 4대 지수
# =========================

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
        return {"현재값": last, "전일종가": prev_close, "등락률": change_pct, "상태": "자동"}
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

# =========================
# 종목 유니버스
# =========================

STOCK_UNIVERSE = [
    # 반도체/AI
    {"종목": "삼성전자", "코드": "005930", "별칭": ["삼성전자", "삼전", "Samsung Electronics"], "테마": "반도체/AI"},
    {"종목": "SK하이닉스", "코드": "000660", "별칭": ["SK하이닉스", "하이닉스", "SK hynix"], "테마": "반도체/AI"},
    {"종목": "한미반도체", "코드": "042700", "별칭": ["한미반도체", "Hanmi Semiconductor"], "테마": "HBM 장비"},
    {"종목": "이수페타시스", "코드": "007660", "별칭": ["이수페타시스", "Isu Petasys"], "테마": "AI PCB"},
    {"종목": "오픈엣지테크놀로지", "코드": "394280", "별칭": ["오픈엣지테크놀로지", "오픈엣지"], "테마": "AI 반도체"},
    {"종목": "DB하이텍", "코드": "000990", "별칭": ["DB하이텍"], "테마": "반도체"},
    {"종목": "리노공업", "코드": "058470", "별칭": ["리노공업"], "테마": "반도체 장비"},
    {"종목": "HPSP", "코드": "403870", "별칭": ["HPSP"], "테마": "반도체 장비"},
    {"종목": "솔브레인", "코드": "357780", "별칭": ["솔브레인"], "테마": "반도체 소재"},
    {"종목": "동진쎄미켐", "코드": "005290", "별칭": ["동진쎄미켐"], "테마": "반도체 소재"},

    # 전력/인프라
    {"종목": "HD현대일렉트릭", "코드": "267260", "별칭": ["HD현대일렉트릭", "현대일렉트릭"], "테마": "전력기기"},
    {"종목": "효성중공업", "코드": "298040", "별칭": ["효성중공업"], "테마": "전력기기"},
    {"종목": "LS ELECTRIC", "코드": "010120", "별칭": ["LS ELECTRIC", "LS일렉트릭", "엘에스일렉트릭"], "테마": "전력기기"},
    {"종목": "일진전기", "코드": "103590", "별칭": ["일진전기"], "테마": "전력기기"},
    {"종목": "두산에너빌리티", "코드": "034020", "별칭": ["두산에너빌리티"], "테마": "원전/전력"},

    # 방산
    {"종목": "한화에어로스페이스", "코드": "012450", "별칭": ["한화에어로스페이스", "한화에어로"], "테마": "방산"},
    {"종목": "현대로템", "코드": "064350", "별칭": ["현대로템"], "테마": "방산/철도"},
    {"종목": "한국항공우주", "코드": "047810", "별칭": ["한국항공우주", "KAI"], "테마": "방산"},
    {"종목": "LIG넥스원", "코드": "079550", "별칭": ["LIG넥스원", "엘아이지넥스원"], "테마": "방산"},

    # 로봇/AI
    {"종목": "레인보우로보틱스", "코드": "277810", "별칭": ["레인보우로보틱스"], "테마": "로봇"},
    {"종목": "두산로보틱스", "코드": "454910", "별칭": ["두산로보틱스"], "테마": "로봇"},
    {"종목": "로보티즈", "코드": "108490", "별칭": ["로보티즈"], "테마": "로봇"},
    {"종목": "로보스타", "코드": "090360", "별칭": ["로보스타"], "테마": "로봇"},

    # 바이오
    {"종목": "삼성바이오로직스", "코드": "207940", "별칭": ["삼성바이오로직스", "삼바"], "테마": "바이오"},
    {"종목": "셀트리온", "코드": "068270", "별칭": ["셀트리온"], "테마": "바이오"},
    {"종목": "알테오젠", "코드": "196170", "별칭": ["알테오젠"], "테마": "바이오"},
    {"종목": "리가켐바이오", "코드": "141080", "별칭": ["리가켐바이오"], "테마": "바이오"},

    # 2차전지/자동차
    {"종목": "LG에너지솔루션", "코드": "373220", "별칭": ["LG에너지솔루션", "엘지에너지솔루션"], "테마": "2차전지"},
    {"종목": "삼성SDI", "코드": "006400", "별칭": ["삼성SDI"], "테마": "2차전지"},
    {"종목": "에코프로비엠", "코드": "247540", "별칭": ["에코프로비엠"], "테마": "2차전지"},
    {"종목": "현대차", "코드": "005380", "별칭": ["현대차", "현대자동차"], "테마": "자동차"},
    {"종목": "기아", "코드": "000270", "별칭": ["기아"], "테마": "자동차"},

    # 금융/지주
    {"종목": "KB금융", "코드": "105560", "별칭": ["KB금융"], "테마": "금융"},
    {"종목": "신한지주", "코드": "055550", "별칭": ["신한지주"], "테마": "금융"},
    {"종목": "하나금융지주", "코드": "086790", "별칭": ["하나금융지주"], "테마": "금융"},
    {"종목": "메리츠금융지주", "코드": "138040", "별칭": ["메리츠금융지주"], "테마": "금융"},
]

DISCOVERY_QUERIES = [
    "코스피 주식 급등",
    "코스닥 주식 급등",
    "국내 증시 특징주",
    "오늘의 특징주",
    "증시 급등주",
    "주식 수급 특징주",
    "AI 반도체 주식",
    "방산 수출 주식",
    "전력기기 주식",
    "로봇 관련주",
    "바이오 특징주",
    "2차전지 특징주",
]

GUDO_WATCHLIST = [
    "삼성전자", "SK하이닉스", "한미반도체", "이수페타시스", "오픈엣지테크놀로지",
    "HD현대일렉트릭", "효성중공업", "LS ELECTRIC", "한화에어로스페이스",
    "현대로템", "레인보우로보틱스", "두산로보틱스"
]

GOOD_WORDS = ["급등", "상승", "수주", "계약", "증설", "공급", "상향", "호실적", "AI", "HBM", "데이터센터", "수출", "신고가", "랠리", "반등"]
BAD_WORDS = ["급락", "하락", "소송", "적자", "하향", "감산", "규제", "압수수색", "유증", "전환사채", "상폐", "부진"]

# =========================
# 뉴스 수집
# =========================

@st.cache_data(ttl=300)
def fetch_google_news(query):
    try:
        url = f"https://news.google.com/rss/search?q={quote(query)}&hl=ko&gl=KR&ceid=KR:ko"
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        if res.status_code != 200:
            return []
        root = ET.fromstring(res.content)
        items = root.findall(".//item")
        out = []
        for item in items[:20]:
            title = item.findtext("title") or ""
            link = item.findtext("link") or ""
            pub = item.findtext("pubDate") or ""
            out.append({"source": "Google", "title": title, "text": title, "link": link, "pubDate": pub})
        return out
    except Exception:
        return []

@st.cache_data(ttl=300)
def fetch_naver_news(query):
    try:
        url = f"https://newssearch.naver.com/search.naver?where=rss&query={quote(query)}"
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        if res.status_code != 200:
            return []
        root = ET.fromstring(res.content)
        items = root.findall(".//item")
        out = []
        for item in items[:20]:
            title = item.findtext("title") or ""
            desc = item.findtext("description") or ""
            link = item.findtext("link") or ""
            pub = item.findtext("pubDate") or ""
            clean_title = title.replace("<b>", "").replace("</b>", "")
            clean_desc = desc.replace("<b>", "").replace("</b>", "")
            out.append({"source": "Naver", "title": clean_title, "text": clean_title + " " + clean_desc, "link": link, "pubDate": pub})
        return out
    except Exception:
        return []

def discover_top10():
    all_news = []
    for q in DISCOVERY_QUERIES:
        all_news.extend(fetch_google_news(q))
        all_news.extend(fetch_naver_news(q))

    rows = []
    samples = {}
    for stock in STOCK_UNIVERSE:
        score = 0
        mentions = 0
        good = 0
        bad = 0
        source_naver = 0
        source_google = 0
        stock_samples = []

        for n in all_news:
            text = n["text"]
            hit = any(alias.lower() in text.lower() for alias in stock["별칭"])
            if not hit:
                continue

            mentions += 1
            if n["source"] == "Naver":
                source_naver += 1
            if n["source"] == "Google":
                source_google += 1

            good += sum(text.count(w) for w in GOOD_WORDS)
            bad += sum(text.count(w) for w in BAD_WORDS)

            if len(stock_samples) < 4:
                stock_samples.append(f"[{n['source']}] {n['title']}")

        if mentions > 0:
            score = min(100, int(mentions * 11 + good * 4 - bad * 5 + (8 if source_naver and source_google else 0)))
            if score >= 80:
                stage = "관심 급증"
            elif score >= 60:
                stage = "관심 상승"
            elif score >= 35:
                stage = "관찰"
            else:
                stage = "약함"

            rows.append({
                "종목": stock["종목"],
                "코드": stock["코드"],
                "테마": stock["테마"],
                "관심도점수": score,
                "언급수": mentions,
                "네이버": source_naver,
                "구글": source_google,
                "긍정키워드": good,
                "부정키워드": bad,
                "단계": stage,
            })
            samples[stock["종목"]] = stock_samples

    df = pd.DataFrame(rows)
    if df.empty:
        return df, samples
    return df.sort_values(["관심도점수", "언급수"], ascending=False).head(10), samples

def gudo_tab_data(top10_df):
    base = pd.DataFrame([s for s in STOCK_UNIVERSE if s["종목"] in GUDO_WATCHLIST])
    if top10_df.empty:
        base["관심도점수"] = 0
        base["언급수"] = 0
        base["단계"] = "대기"
    else:
        base = base.merge(top10_df[["종목", "관심도점수", "언급수", "단계"]], on="종목", how="left")
        base[["관심도점수", "언급수"]] = base[["관심도점수", "언급수"]].fillna(0)
        base["단계"] = base["단계"].fillna("대기")
    base["구도관점"] = base["종목"].apply(lambda x: "구도 스타일 후보군")
    return base.sort_values("관심도점수", ascending=False)

# =========================
# UI
# =========================

if st.button("🔄 전체 새로고침"):
    st.cache_data.clear()
    st.rerun()

idx = calc_index_rows()
idx_total = idx["TAO 추정 기여"].sum()

tab1, tab2, tab3, tab4 = st.tabs(["🌏 글로벌 지수", "🔥 자동 TOP10", "🧠 구도 후보", "📌 설명"])

with tab1:
    st.subheader("4대 지수 자동 조회")
    cols = st.columns(4)
    for i, r in idx.iterrows():
        with cols[i]:
            value = "-" if pd.isna(r["현재값"]) else f"{r['현재값']:,.2f}"
            delta = "데이터 대기" if r["상태"] != "자동" else f"{r['등락률']:+.2f}%"
            st.metric(f"{r['지역']} · {r['지수']}", value, delta)
            st.caption(f"{r['신호']} · {r['메모']}")

    show = idx.copy()
    show["현재값"] = show["현재값"].apply(lambda x: "-" if pd.isna(x) else f"{x:,.2f}")
    show["전일종가"] = show["전일종가"].apply(lambda x: "-" if pd.isna(x) else f"{x:,.2f}")
    show["등락률"] = show["등락률"].apply(lambda x: f"{x:+.2f}%")
    show["가중치"] = show["가중치"].apply(lambda x: f"{x*100:.0f}%")
    show["TAO 추정 기여"] = show["TAO 추정 기여"].apply(lambda x: f"{x:+.2f}%p")
    st.dataframe(show, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("뉴스 기반 자동 관심종목 TOP10")
    st.caption("내가 종목을 고정하지 않고, 네이버+구글 뉴스에서 많이 언급된 종목을 자동으로 집계합니다.")

    top10, samples = discover_top10()

    if top10.empty:
        st.warning("아직 TOP10을 만들 만큼 뉴스 데이터를 가져오지 못했습니다. 새로고침하거나 잠시 뒤 다시 확인해보세요.")
    else:
        cols = st.columns(5)
        for i, r in top10.head(5).reset_index(drop=True).iterrows():
            with cols[i]:
                st.metric(f"{i+1}. {r['종목']}", f"{r['관심도점수']}점", r["단계"])
                st.caption(f"{r['테마']} · 언급 {int(r['언급수'])}건")

        st.divider()
        st.dataframe(top10, use_container_width=True, hide_index=True)

        st.subheader("TOP 종목 뉴스 샘플")
        for _, r in top10.head(5).iterrows():
            with st.expander(f"{r['종목']} · {r['관심도점수']}점 · {r['단계']}"):
                for s in samples.get(r["종목"], []):
                    st.write("• " + s)

with tab3:
    st.subheader("구도 후보 탭")
    st.caption("자동 TOP10과 별도로, 구도 스타일 후보군만 따로 모아 보는 탭입니다.")

    top10, _ = discover_top10()
    gd = gudo_tab_data(top10)

    st.dataframe(gd[["종목", "코드", "테마", "관심도점수", "언급수", "단계", "구도관점"]], use_container_width=True, hide_index=True)

    avg = 0 if gd.empty else gd["관심도점수"].head(5).mean()
    signal = int(max(0, min(100, avg * 0.7 + (50 + idx_total * 10) * 0.3)))

    c1, c2, c3 = st.columns(3)
    c1.metric("구도 후보 평균점수", f"{avg:.0f}점")
    c2.metric("4대 지수 영향", f"{idx_total:+.2f}%")
    c3.metric("구도 종합 시그널", f"{signal}점")

with tab4:
    st.subheader("작동 방식")
    st.markdown("""
    ### 자동 TOP10
    - 네이버 뉴스와 구글 뉴스를 동시에 검색
    - 국내 주요 종목 유니버스에서 뉴스 제목/본문에 많이 등장한 종목을 집계
    - 언급수, 긍정 키워드, 부정 키워드, 네이버/구글 동시 출현 여부로 점수화

    ### 구도 후보
    - 자동 TOP10과 별도로 구도 스타일 후보군을 따로 추적
    - 반도체, HBM, 전력기기, 방산, 로봇 등 구도 스타일 후보를 별도 표시

    ### 주의
    - 매수/매도 신호가 아니라 조사 시작 신호
    - 실제 구도 보유 종목을 알 수는 없음
    - 뉴스 데이터가 막히면 점수가 낮게 나올 수 있음
    """)

st.caption("태형레이더는 투자 자문이 아니라 시장 관심도와 구도 스타일 후보를 탐색하는 개인용 분석 도구입니다.")
