import streamlit as st
import pandas as pd
from datetime import datetime, time
from zoneinfo import ZoneInfo

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
st.caption("시장 시간대별 자동 전환 · 한국/미국/일본/대만 실시간 레이더")

# =====================
# 설정
# =====================

with st.sidebar:
    st.header("⚙️ 설정")
    refresh_sec = st.selectbox("자동 새로고침 주기", [30, 60, 120, 300], index=1)
    auto_refresh = st.toggle("자동 새로고침", value=True)
    st.caption("무료 데이터라 실제 거래소 실시간보다 지연될 수 있습니다.")

if auto_refresh and AUTOREFRESH_OK:
    st_autorefresh(interval=refresh_sec * 1000, key="radar_refresh")

if st.button("🔄 즉시 새로고침"):
    st.cache_data.clear()
    st.rerun()

# =====================
# 시장 시간
# =====================

MARKET_HOURS = {
    "한국": {"tz": "Asia/Seoul", "open": time(9, 0), "close": time(15, 30), "emoji": "🇰🇷"},
    "일본": {"tz": "Asia/Tokyo", "open": time(9, 0), "close": time(15, 30), "emoji": "🇯🇵"},
    "대만": {"tz": "Asia/Taipei", "open": time(9, 0), "close": time(13, 30), "emoji": "🇹🇼"},
    "미국": {"tz": "America/New_York", "open": time(9, 30), "close": time(16, 0), "emoji": "🇺🇸"},
}

def is_market_open(market):
    info = MARKET_HOURS[market]
    now = datetime.now(ZoneInfo(info["tz"]))
    if now.weekday() >= 5:
        return False, now
    return info["open"] <= now.time() <= info["close"], now

def active_market():
    open_markets = []
    for m in MARKET_HOURS:
        opened, now = is_market_open(m)
        if opened:
            open_markets.append((m, now))
    if open_markets:
        # 한국/일본/대만/미국 순서가 아니라 실제 열린 시장 중 첫 번째
        return open_markets[0][0], open_markets
    # 열려 있는 장이 없으면 미국 → 한국 → 일본 → 대만 순으로 최근 확인 대상
    return "미국", open_markets

# =====================
# 종목 유니버스
# =====================

MARKET_INDEXES = {
    "한국": {"지수": "KOSPI", "티커": "^KS11"},
    "미국": {"지수": "NASDAQ", "티커": "^IXIC"},
    "일본": {"지수": "Nikkei 225", "티커": "^N225"},
    "대만": {"지수": "TAIEX", "티커": "^TWII"},
}

UNIVERSE = {
    "한국": [
        {"종목":"삼성전자","티커":"005930.KS","테마":"반도체/AI"},
        {"종목":"SK하이닉스","티커":"000660.KS","테마":"반도체/AI"},
        {"종목":"한미반도체","티커":"042700.KS","테마":"HBM 장비"},
        {"종목":"이수페타시스","티커":"007660.KS","테마":"AI PCB"},
        {"종목":"HD현대일렉트릭","티커":"267260.KS","테마":"전력기기"},
        {"종목":"효성중공업","티커":"298040.KS","테마":"전력기기"},
        {"종목":"LS ELECTRIC","티커":"010120.KS","테마":"전력기기"},
        {"종목":"한화에어로스페이스","티커":"012450.KS","테마":"방산"},
        {"종목":"현대로템","티커":"064350.KS","테마":"방산"},
        {"종목":"레인보우로보틱스","티커":"277810.KQ","테마":"로봇"},
        {"종목":"두산로보틱스","티커":"454910.KS","테마":"로봇"},
        {"종목":"알테오젠","티커":"196170.KQ","테마":"바이오"},
        {"종목":"셀트리온","티커":"068270.KS","테마":"바이오"},
        {"종목":"LG에너지솔루션","티커":"373220.KS","테마":"2차전지"},
        {"종목":"에코프로비엠","티커":"247540.KQ","테마":"2차전지"},
    ],
    "미국": [
        {"종목":"NVIDIA","티커":"NVDA","테마":"AI 반도체"},
        {"종목":"Micron","티커":"MU","테마":"메모리"},
        {"종목":"Broadcom","티커":"AVGO","테마":"AI 네트워크"},
        {"종목":"AMD","티커":"AMD","테마":"AI 반도체"},
        {"종목":"TSMC ADR","티커":"TSM","테마":"파운드리"},
        {"종목":"ASML","티커":"ASML","테마":"반도체 장비"},
        {"종목":"Lam Research","티커":"LRCX","테마":"반도체 장비"},
        {"종목":"Applied Materials","티커":"AMAT","테마":"반도체 장비"},
        {"종목":"Super Micro","티커":"SMCI","테마":"AI 서버"},
        {"종목":"Palantir","티커":"PLTR","테마":"AI 소프트웨어"},
        {"종목":"Microsoft","티커":"MSFT","테마":"AI/클라우드"},
        {"종목":"Meta","티커":"META","테마":"AI/플랫폼"},
        {"종목":"Tesla","티커":"TSLA","테마":"전기차/AI"},
        {"종목":"Apple","티커":"AAPL","테마":"빅테크"},
        {"종목":"Amazon","티커":"AMZN","테마":"클라우드/AI"},
    ],
    "일본": [
        {"종목":"Tokyo Electron","티커":"8035.T","테마":"반도체 장비"},
        {"종목":"Advantest","티커":"6857.T","테마":"반도체 테스트"},
        {"종목":"Disco","티커":"6146.T","테마":"반도체 장비"},
        {"종목":"Renesas","티커":"6723.T","테마":"반도체"},
        {"종목":"SoftBank Group","티커":"9984.T","테마":"AI 투자"},
        {"종목":"Sony","티커":"6758.T","테마":"전자/센서"},
        {"종목":"Toyota","티커":"7203.T","테마":"자동차"},
        {"종목":"Hitachi","티커":"6501.T","테마":"전력/인프라"},
        {"종목":"Mitsubishi Heavy","티커":"7011.T","테마":"방산/중공업"},
        {"종목":"Fujitsu","티커":"6702.T","테마":"IT"},
    ],
    "대만": [
        {"종목":"TSMC","티커":"2330.TW","테마":"파운드리/AI"},
        {"종목":"MediaTek","티커":"2454.TW","테마":"반도체"},
        {"종목":"Foxconn","티커":"2317.TW","테마":"AI 서버/전자"},
        {"종목":"Quanta","티커":"2382.TW","테마":"AI 서버"},
        {"종목":"Wistron","티커":"3231.TW","테마":"AI 서버"},
        {"종목":"Inventec","티커":"2356.TW","테마":"AI 서버"},
        {"종목":"ASE Technology","티커":"3711.TW","테마":"패키징"},
        {"종목":"Delta Electronics","티커":"2308.TW","테마":"전력/부품"},
        {"종목":"GlobalWafers","티커":"6488.TWO","테마":"웨이퍼"},
        {"종목":"Novatek","티커":"3034.TW","테마":"반도체"},
    ],
}

GUDO_NAMES = ["삼성전자", "SK하이닉스", "한미반도체", "이수페타시스", "HD현대일렉트릭", "효성중공업", "LS ELECTRIC", "한화에어로스페이스", "현대로템", "레인보우로보틱스", "두산로보틱스"]

# =====================
# 데이터 수집
# =====================

@st.cache_data(ttl=60)
def fetch_price(ticker):
    if not YF_OK:
        return None
    try:
        obj = yf.Ticker(ticker)
        intra = obj.history(period="2d", interval="1m", prepost=True)
        daily = obj.history(period="20d", interval="1d")

        if daily is None or daily.empty:
            return None

        if intra is not None and not intra.empty:
            last = float(intra["Close"].dropna().iloc[-1])
            volume_today = float(intra["Volume"].dropna().sum())
        else:
            last = float(daily["Close"].dropna().iloc[-1])
            volume_today = float(daily["Volume"].dropna().iloc[-1])

        closes = daily["Close"].dropna()
        vols = daily["Volume"].dropna()

        if len(closes) < 2:
            return None

        prev_close = float(closes.iloc[-2])
        change_pct = (last / prev_close - 1) * 100

        avg_vol = float(vols.tail(10).mean()) if len(vols) >= 3 else float(vols.mean())
        vol_ratio = volume_today / avg_vol if avg_vol > 0 else 0

        return {
            "현재가": last,
            "등락률": change_pct,
            "거래량비율": vol_ratio,
            "상태": "자동",
        }
    except Exception:
        return None

def calc_score(change, vol_ratio):
    price_score = min(35, abs(change) * 5)
    volume_score = min(50, vol_ratio * 22)
    direction_bonus = 10 if change > 0 else 0
    return int(max(0, min(100, price_score + volume_score + direction_bonus)))

def calc_market_top(market):
    rows = []
    for s in UNIVERSE[market]:
        live = fetch_price(s["티커"])
        if live:
            score = calc_score(live["등락률"], live["거래량비율"])
            stage = "관심 급증" if score >= 80 else "관심 상승" if score >= 60 else "관찰" if score >= 35 else "약함"
            rows.append({**s, **live, "관심도점수": score, "단계": stage})
        else:
            rows.append({**s, "현재가": None, "등락률": 0.0, "거래량비율": 0.0, "상태": "대기", "관심도점수": 0, "단계": "대기"})
    df = pd.DataFrame(rows)
    return df.sort_values(["관심도점수", "거래량비율", "등락률"], ascending=False).head(10)

def get_index_row(market):
    idx = MARKET_INDEXES[market]
    live = fetch_price(idx["티커"])
    if live:
        return idx["지수"], live["현재가"], live["등락률"]
    return idx["지수"], None, 0.0

# =====================
# UI
# =====================

current_market, open_markets = active_market()

open_text = ", ".join([f"{MARKET_HOURS[m]['emoji']} {m}" for m, _ in open_markets]) if open_markets else "현재 정규장 열림 없음"
now_kst = datetime.now(ZoneInfo("Asia/Seoul"))

st.info(f"현재 활성 시장: {MARKET_HOURS[current_market]['emoji']} **{current_market}** · 열린 시장: {open_text} · KST {now_kst.strftime('%H:%M:%S')}")

tab_home, tab_kr, tab_us, tab_jp, tab_tw, tab_gudo = st.tabs(["🏠 홈", "🇰🇷 한국", "🇺🇸 미국", "🇯🇵 일본", "🇹🇼 대만", "🧠 구도 후보"])

with tab_home:
    st.subheader(f"{MARKET_HOURS[current_market]['emoji']} 활성 시장 TOP10")

    idx_name, idx_value, idx_change = get_index_row(current_market)
    c1, c2, c3 = st.columns(3)
    c1.metric(f"{current_market} 지수 · {idx_name}", "-" if idx_value is None else f"{idx_value:,.2f}", f"{idx_change:+.2f}%")
    c2.metric("업데이트", now_kst.strftime("%H:%M:%S"))
    c3.metric("자동 새로고침", f"{refresh_sec}초")

    top = calc_market_top(current_market)

    cols = st.columns(5)
    for i, r in top.head(5).reset_index(drop=True).iterrows():
        with cols[i]:
            price = "-" if pd.isna(r["현재가"]) else f"{r['현재가']:,.2f}"
            st.metric(f"{i+1}. {r['종목']}", f"{int(r['관심도점수'])}점", f"{r['등락률']:+.2f}%")
            st.caption(f"{r['테마']} · 거래 {r['거래량비율']:.1f}배")

    st.divider()
    view = top.copy()
    view["현재가"] = view["현재가"].apply(lambda x: "-" if pd.isna(x) else f"{x:,.2f}")
    view["등락률"] = view["등락률"].apply(lambda x: f"{x:+.2f}%")
    view["거래량비율"] = view["거래량비율"].apply(lambda x: f"{x:.1f}배")
    st.dataframe(view, use_container_width=True, hide_index=True)

def render_market(market):
    idx_name, idx_value, idx_change = get_index_row(market)
    st.subheader(f"{MARKET_HOURS[market]['emoji']} {market} 시장 TOP10")
    st.metric(f"{idx_name}", "-" if idx_value is None else f"{idx_value:,.2f}", f"{idx_change:+.2f}%")

    top = calc_market_top(market)
    view = top.copy()
    view["현재가"] = view["현재가"].apply(lambda x: "-" if pd.isna(x) else f"{x:,.2f}")
    view["등락률"] = view["등락률"].apply(lambda x: f"{x:+.2f}%")
    view["거래량비율"] = view["거래량비율"].apply(lambda x: f"{x:.1f}배")
    st.dataframe(view, use_container_width=True, hide_index=True)

with tab_kr:
    render_market("한국")

with tab_us:
    render_market("미국")

with tab_jp:
    render_market("일본")

with tab_tw:
    render_market("대만")

with tab_gudo:
    st.subheader("구도 후보")
    kr_top = calc_market_top("한국")
    gd = kr_top[kr_top["종목"].isin(GUDO_NAMES)].copy()

    if gd.empty:
        gd = pd.DataFrame([s for s in UNIVERSE["한국"] if s["종목"] in GUDO_NAMES])
        gd["현재가"] = None
        gd["등락률"] = 0.0
        gd["거래량비율"] = 0.0
        gd["관심도점수"] = 0
        gd["단계"] = "대기"

    view = gd.copy()
    view["현재가"] = view["현재가"].apply(lambda x: "-" if pd.isna(x) else f"{x:,.2f}")
    view["등락률"] = view["등락률"].apply(lambda x: f"{x:+.2f}%")
    view["거래량비율"] = view["거래량비율"].apply(lambda x: f"{x:.1f}배")
    st.dataframe(view, use_container_width=True, hide_index=True)

    avg = 0 if gd.empty else gd["관심도점수"].mean()
    st.metric("구도 후보 평균 관심도", f"{avg:.0f}점")

st.caption("무료 공개 데이터 기반이라 지연·누락 가능성이 있습니다. 태형레이더는 시장 관심도 탐색용 도구입니다.")
