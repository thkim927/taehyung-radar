import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote
from datetime import datetime

st.set_page_config(page_title="태형레이더", page_icon="📡", layout="wide")

try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_OK = True
except Exception:
    AUTOREFRESH_OK = False

try:
    import yfinance as yf
    YF_OK = True
except Exception:
    YF_OK = False

st.title("📡 태형레이더 Realtime")
st.caption("4대 지수 + 가격/거래량 + 뉴스 언급량 기반 실시간 관심종목 TOP10")

# =====================
# 자동 새로고침
# =====================

with st.sidebar:
    st.header("설정")
    refresh_sec = st.selectbox("자동 새로고침", [30, 60, 120, 300], index=1)
    use_auto = st.toggle("자동 새로고침 사용", value=True)
    st.caption("무료 데이터라 실제 거래소 실시간보다 지연될 수 있습니다.")

if use_auto and AUTOREFRESH_OK:
    st_autorefresh(interval=refresh_sec * 1000, key="radar_refresh")

if st.button("🔄 즉시 새로고침"):
    st.cache_data.clear()
    st.rerun()

# =====================
# 지수
# =====================

INDEXES = [
    {"지역": "미국", "지수": "NASDAQ", "티커": "^IXIC", "가중치": 0.35, "메모": "미국 AI·성장주 선행 신호"},
    {"지역": "한국", "지수": "KOSPI", "티커": "^KS11", "가중치": 0.35, "메모": "TAO 직접 영향 가능성"},
    {"지역": "일본", "지수": "Nikkei 225", "티커": "^N225", "가중치": 0.15, "메모": "아시아 위험선호"},
    {"지역": "대만", "지수": "TAIEX", "티커": "^TWII", "가중치": 0.15, "메모": "TSMC·AI 반도체 밸류체인"},
]

# 국내 주요 유니버스. 처음은 넓게 시작하고 계속 늘리면 됨.
STOCKS = [
    # 반도체/AI
    {"종목":"삼성전자","코드":"005930","티커":"005930.KS","테마":"반도체/AI","별칭":["삼성전자","삼전","Samsung Electronics"]},
    {"종목":"SK하이닉스","코드":"000660","티커":"000660.KS","테마":"반도체/AI","별칭":["SK하이닉스","하이닉스","SK hynix"]},
    {"종목":"한미반도체","코드":"042700","티커":"042700.KS","테마":"HBM 장비","별칭":["한미반도체","Hanmi Semiconductor"]},
    {"종목":"이수페타시스","코드":"007660","티커":"007660.KS","테마":"AI PCB","별칭":["이수페타시스","Isu Petasys"]},
    {"종목":"오픈엣지테크놀로지","코드":"394280","티커":"394280.KQ","테마":"AI 반도체","별칭":["오픈엣지테크놀로지","오픈엣지"]},
    {"종목":"DB하이텍","코드":"000990","티커":"000990.KS","테마":"반도체","별칭":["DB하이텍"]},
    {"종목":"리노공업","코드":"058470","티커":"058470.KQ","테마":"반도체 장비","별칭":["리노공업"]},
    {"종목":"HPSP","코드":"403870","티커":"403870.KQ","테마":"반도체 장비","별칭":["HPSP"]},
    {"종목":"솔브레인","코드":"357780","티커":"357780.KQ","테마":"반도체 소재","별칭":["솔브레인"]},
    {"종목":"동진쎄미켐","코드":"005290","티커":"005290.KQ","테마":"반도체 소재","별칭":["동진쎄미켐"]},

    # 전력/인프라
    {"종목":"HD현대일렉트릭","코드":"267260","티커":"267260.KS","테마":"전력기기","별칭":["HD현대일렉트릭","현대일렉트릭"]},
    {"종목":"효성중공업","코드":"298040","티커":"298040.KS","테마":"전력기기","별칭":["효성중공업"]},
    {"종목":"LS ELECTRIC","코드":"010120","티커":"010120.KS","테마":"전력기기","별칭":["LS ELECTRIC","LS일렉트릭","엘에스일렉트릭"]},
    {"종목":"일진전기","코드":"103590","티커":"103590.KS","테마":"전력기기","별칭":["일진전기"]},
    {"종목":"두산에너빌리티","코드":"034020","티커":"034020.KS","테마":"원전/전력","별칭":["두산에너빌리티"]},

    # 방산
    {"종목":"한화에어로스페이스","코드":"012450","티커":"012450.KS","테마":"방산","별칭":["한화에어로스페이스","한화에어로"]},
    {"종목":"현대로템","코드":"064350","티커":"064350.KS","테마":"방산/철도","별칭":["현대로템"]},
    {"종목":"한국항공우주","코드":"047810","티커":"047810.KS","테마":"방산","별칭":["한국항공우주","KAI"]},
    {"종목":"LIG넥스원","코드":"079550","티커":"079550.KS","테마":"방산","별칭":["LIG넥스원","엘아이지넥스원"]},

    # 로봇
    {"종목":"레인보우로보틱스","코드":"277810","티커":"277810.KQ","테마":"로봇","별칭":["레인보우로보틱스"]},
    {"종목":"두산로보틱스","코드":"454910","티커":"454910.KS","테마":"로봇","별칭":["두산로보틱스"]},
    {"종목":"로보티즈","코드":"108490","티커":"108490.KQ","테마":"로봇","별칭":["로보티즈"]},
    {"종목":"로보스타","코드":"090360","티커":"090360.KQ","테마":"로봇","별칭":["로보스타"]},

    # 바이오
    {"종목":"삼성바이오로직스","코드":"207940","티커":"207940.KS","테마":"바이오","별칭":["삼성바이오로직스","삼바"]},
    {"종목":"셀트리온","코드":"068270","티커":"068270.KS","테마":"바이오","별칭":["셀트리온"]},
    {"종목":"알테오젠","코드":"196170","티커":"196170.KQ","테마":"바이오","별칭":["알테오젠"]},
    {"종목":"리가켐바이오","코드":"141080","티커":"141080.KQ","테마":"바이오","별칭":["리가켐바이오"]},

    # 2차전지/자동차
    {"종목":"LG에너지솔루션","코드":"373220","티커":"373220.KS","테마":"2차전지","별칭":["LG에너지솔루션","엘지에너지솔루션"]},
    {"종목":"삼성SDI","코드":"006400","티커":"006400.KS","테마":"2차전지","별칭":["삼성SDI"]},
    {"종목":"에코프로비엠","코드":"247540","티커":"247540.KQ","테마":"2차전지","별칭":["에코프로비엠"]},
    {"종목":"현대차","코드":"005380","티커":"005380.KS","테마":"자동차","별칭":["현대차","현대자동차"]},
    {"종목":"기아","코드":"000270","티커":"000270.KS","테마":"자동차","별칭":["기아"]},

    # 금융/지주
    {"종목":"KB금융","코드":"105560","티커":"105560.KS","테마":"금융","별칭":["KB금융"]},
    {"종목":"신한지주","코드":"055550","티커":"055550.KS","테마":"금융","별칭":["신한지주"]},
    {"종목":"하나금융지주","코드":"086790","티커":"086790.KS","테마":"금융","별칭":["하나금융지주"]},
    {"종목":"메리츠금융지주","코드":"138040","티커":"138040.KS","테마":"금융","별칭":["메리츠금융지주"]},
]

GUDO_WATCHLIST = [
    "삼성전자", "SK하이닉스", "한미반도체", "이수페타시스", "오픈엣지테크놀로지",
    "HD현대일렉트릭", "효성중공업", "LS ELECTRIC", "한화에어로스페이스",
    "현대로템", "레인보우로보틱스", "두산로보틱스"
]

DISCOVERY_QUERIES = [
    "코스피 특징주", "코스닥 특징주", "오늘 특징주", "국내 증시 급등주",
    "주식 수급 특징주", "AI 반도체 주식", "방산 수출 주식", "전력기기 주식",
    "로봇 관련주", "바이오 특징주", "2차전지 특징주"
]

GOOD_WORDS = ["급등", "상승", "수주", "계약", "증설", "공급", "상향", "호실적", "AI", "HBM", "데이터센터", "수출", "신고가", "랠리", "반등"]
BAD_WORDS = ["급락", "하락", "소송", "적자", "하향", "감산", "규제", "압수수색", "유증", "전환사채", "상폐", "부진"]

# =====================
# 데이터 함수
# =====================

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

@st.cache_data(ttl=60)
def fetch_stock(ticker):
    if not YF_OK:
        return None
    try:
        obj = yf.Ticker(ticker)
        intra = obj.history(period="2d", interval="1m", prepost=False)
        daily = obj.history(period="20d", interval="1d")
        if daily is None or daily.empty:
            return None

        if intra is not None and not intra.empty:
            last_price = float(intra["Close"].dropna().iloc[-1])
            today_volume = float(intra["Volume"].dropna().sum())
        else:
            last_price = float(daily["Close"].dropna().iloc[-1])
            today_volume = float(daily["Volume"].dropna().iloc[-1])

        closes = daily["Close"].dropna()
        vols = daily["Volume"].dropna()

        if len(closes) < 2:
            return None

        prev_close = float(closes.iloc[-2])
        change_pct = (last_price / prev_close - 1) * 100

        avg_vol = float(vols.tail(10).mean()) if len(vols) >= 3 else float(vols.mean())
        volume_ratio = today_volume / avg_vol if avg_vol > 0 else 0

        return {
            "현재가": last_price,
            "등락률": change_pct,
            "거래량비율": volume_ratio,
            "상태": "자동",
        }
    except Exception:
        return None

@st.cache_data(ttl=300)
def fetch_google_news(query):
    try:
        url = f"https://news.google.com/rss/search?q={quote(query)}&hl=ko&gl=KR&ceid=KR:ko"
        res = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=8)
        if res.status_code != 200:
            return []
        root = ET.fromstring(res.content)
        items = root.findall(".//item")
        out = []
        for item in items[:20]:
            title = item.findtext("title") or ""
            link = item.findtext("link") or ""
            pub = item.findtext("pubDate") or ""
            out.append({"source":"Google", "title":title, "text":title, "link":link, "pubDate":pub})
        return out
    except Exception:
        return []

@st.cache_data(ttl=300)
def fetch_naver_news(query):
    try:
        url = f"https://newssearch.naver.com/search.naver?where=rss&query={quote(query)}"
        res = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=8)
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
            out.append({"source":"Naver", "title":clean_title, "text":clean_title + " " + clean_desc, "link":link, "pubDate":pub})
        return out
    except Exception:
        return []

@st.cache_data(ttl=300)
def get_news_pool():
    pool = []
    for q in DISCOVERY_QUERIES:
        pool.extend(fetch_google_news(q))
        pool.extend(fetch_naver_news(q))
    return pool

def index_signal(change):
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
            rows.append({**item, **live, "신호": index_signal(live["등락률"])})
        else:
            rows.append({**item, "현재값":None, "전일종가":None, "등락률":0.0, "상태":"대기", "신호":"데이터 대기"})
    df = pd.DataFrame(rows)
    df["TAO 추정 기여"] = df["등락률"] * df["가중치"]
    return df

def calc_top10():
    pool = get_news_pool()
    rows = []
    samples = {}

    for stock in STOCKS:
        live = fetch_stock(stock["티커"])
        if live:
            price = live["현재가"]
            change = live["등락률"]
            vol_ratio = live["거래량비율"]
            data_status = "가격자동"
        else:
            price = None
            change = 0.0
            vol_ratio = 0.0
            data_status = "가격대기"

        mentions = 0
        naver_count = 0
        google_count = 0
        good = 0
        bad = 0
        stock_samples = []

        for n in pool:
            text = n["text"]
            if any(alias.lower() in text.lower() for alias in stock["별칭"]):
                mentions += 1
                if n["source"] == "Naver":
                    naver_count += 1
                else:
                    google_count += 1
                good += sum(text.count(w) for w in GOOD_WORDS)
                bad += sum(text.count(w) for w in BAD_WORDS)
                if len(stock_samples) < 4:
                    stock_samples.append(f"[{n['source']}] {n['title']}")

        # 핵심: 검색/뉴스가 적어도 거래량·등락률로 움직임 포착
        news_score = min(35, mentions * 6 + good * 2 - bad * 3)
        volume_score = min(35, vol_ratio * 18)
        price_score = min(20, abs(change) * 3)
        source_bonus = 5 if naver_count > 0 and google_count > 0 else 0
        total_score = int(max(0, min(100, news_score + volume_score + price_score + source_bonus)))

        if total_score >= 80:
            stage = "관심 급증"
        elif total_score >= 60:
            stage = "관심 상승"
        elif total_score >= 35:
            stage = "관찰"
        else:
            stage = "약함"

        # 너무 약한 것은 제외하되 가격 데이터만 있어도 상위권 후보 가능
        if total_score > 15:
            rows.append({
                "종목": stock["종목"],
                "코드": stock["코드"],
                "테마": stock["테마"],
                "관심도점수": total_score,
                "등락률": change,
                "거래량비율": vol_ratio,
                "뉴스언급": mentions,
                "네이버": naver_count,
                "구글": google_count,
                "긍정": good,
                "부정": bad,
                "단계": stage,
                "상태": data_status,
            })
            samples[stock["종목"]] = stock_samples

    df = pd.DataFrame(rows)
    if df.empty:
        return df, samples
    df = df.sort_values(["관심도점수", "거래량비율", "뉴스언급"], ascending=False).head(10)
    return df, samples

def get_gudo_candidates(top10):
    gudo = pd.DataFrame([s for s in STOCKS if s["종목"] in GUDO_WATCHLIST])
    if top10.empty:
        gudo["관심도점수"] = 0
        gudo["등락률"] = 0.0
        gudo["거래량비율"] = 0.0
        gudo["뉴스언급"] = 0
        gudo["단계"] = "대기"
    else:
        gudo = gudo.merge(top10[["종목","관심도점수","등락률","거래량비율","뉴스언급","단계"]], on="종목", how="left")
        for c in ["관심도점수","등락률","거래량비율","뉴스언급"]:
            gudo[c] = gudo[c].fillna(0)
        gudo["단계"] = gudo["단계"].fillna("대기")
    return gudo.sort_values("관심도점수", ascending=False)

# =====================
# UI
# =====================

idx = calc_index_rows()
idx_total = idx["TAO 추정 기여"].sum()

tab1, tab2, tab3, tab4 = st.tabs(["🌏 글로벌 지수", "🔥 실시간 TOP10", "🧠 구도 후보", "📌 설명"])

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
    st.subheader("실시간 관심종목 TOP10")
    st.caption("뉴스 언급량 + 거래량 급증 + 등락률을 합산해 자동 산출합니다.")

    top10, samples = calc_top10()

    if top10.empty:
        st.warning("아직 TOP10 산출 데이터가 부족합니다. 잠시 후 새로고침해보세요.")
    else:
        cols = st.columns(5)
        for i, r in top10.head(5).reset_index(drop=True).iterrows():
            with cols[i]:
                st.metric(f"{i+1}. {r['종목']}", f"{int(r['관심도점수'])}점", r["단계"])
                st.caption(f"{r['테마']} · {r['등락률']:+.2f}% · 거래 {r['거래량비율']:.1f}배")

        st.divider()

        view = top10.copy()
        view["등락률"] = view["등락률"].apply(lambda x: f"{x:+.2f}%")
        view["거래량비율"] = view["거래량비율"].apply(lambda x: f"{x:.1f}배")
        st.dataframe(view, use_container_width=True, hide_index=True)

        st.subheader("뉴스 샘플")
        for _, r in top10.head(5).iterrows():
            with st.expander(f"{r['종목']} · {r['관심도점수']}점 · {r['단계']}"):
                ss = samples.get(r["종목"], [])
                if ss:
                    for s in ss:
                        st.write("• " + s)
                else:
                    st.write("뉴스 언급은 적지만 가격/거래량 신호로 포착되었습니다.")

with tab3:
    st.subheader("구도 후보 탭")
    top10, _ = calc_top10()
    gd = get_gudo_candidates(top10)

    view = gd[["종목","코드","테마","관심도점수","등락률","거래량비율","뉴스언급","단계"]].copy()
    view["등락률"] = view["등락률"].apply(lambda x: f"{x:+.2f}%")
    view["거래량비율"] = view["거래량비율"].apply(lambda x: f"{x:.1f}배")
    st.dataframe(view, use_container_width=True, hide_index=True)

    avg = 0 if gd.empty else gd["관심도점수"].head(5).mean()
    signal = int(max(0, min(100, avg * 0.7 + (50 + idx_total * 10) * 0.3)))

    c1, c2, c3 = st.columns(3)
    c1.metric("구도 후보 평균점수", f"{avg:.0f}점")
    c2.metric("4대 지수 영향", f"{idx_total:+.2f}%")
    c3.metric("구도 종합 시그널", f"{signal}점")

with tab4:
    st.subheader("작동 방식")
    st.markdown("""
    ### 실시간 TOP10 점수 구조
    - 뉴스 언급량
    - 네이버/구글 뉴스 동시 포착
    - 긍정/부정 키워드
    - 주가 등락률
    - 거래량 급증률

    ### 핵심
    특정 종목을 고정 추천하는 방식이 아니라,  
    **뉴스와 가격/거래량에서 관심도가 올라오는 종목을 자동으로 TOP10에 올립니다.**

    ### 주의
    무료 데이터 기반이라 거래소 공식 실시간보다 지연될 수 있습니다.
    """)

st.caption(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
