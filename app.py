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

st.title("📡 태형레이더 Complete v1")
st.caption("시장시간 자동전환 · 실시간 TOP10 · 거래대금 · 거래량 급증 · 구도 후보 · TAO 시그널")

with st.sidebar:
    st.header("⚙️ 설정")
    refresh_sec = st.selectbox("자동 새로고침", [30, 60, 120, 300], index=1)
    auto_refresh = st.toggle("자동 새로고침 사용", value=True)
    st.caption("무료 공개 데이터 기반이라 실제 거래소보다 지연될 수 있습니다.")

if auto_refresh and AUTOREFRESH_OK:
    st_autorefresh(interval=refresh_sec * 1000, key="radar_refresh")

if st.button("🔄 즉시 새로고침"):
    st.cache_data.clear()
    st.rerun()

MARKET_HOURS = {
    "한국": {"tz": "Asia/Seoul", "open": time(9, 0), "close": time(15, 30), "emoji": "🇰🇷"},
    "일본": {"tz": "Asia/Tokyo", "open": time(9, 0), "close": time(15, 30), "emoji": "🇯🇵"},
    "대만": {"tz": "Asia/Taipei", "open": time(9, 0), "close": time(13, 30), "emoji": "🇹🇼"},
    "미국": {"tz": "America/New_York", "open": time(9, 30), "close": time(16, 0), "emoji": "🇺🇸"},
}

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
        {"종목":"오픈엣지테크놀로지","티커":"394280.KQ","테마":"AI 반도체"},
        {"종목":"DB하이텍","티커":"000990.KS","테마":"반도체"},
        {"종목":"리노공업","티커":"058470.KQ","테마":"반도체 장비"},
        {"종목":"HPSP","티커":"403870.KQ","테마":"반도체 장비"},
        {"종목":"솔브레인","티커":"357780.KQ","테마":"반도체 소재"},
        {"종목":"동진쎄미켐","티커":"005290.KQ","테마":"반도체 소재"},
        {"종목":"HD현대일렉트릭","티커":"267260.KS","테마":"전력기기"},
        {"종목":"효성중공업","티커":"298040.KS","테마":"전력기기"},
        {"종목":"LS ELECTRIC","티커":"010120.KS","테마":"전력기기"},
        {"종목":"일진전기","티커":"103590.KS","테마":"전력기기"},
        {"종목":"두산에너빌리티","티커":"034020.KS","테마":"원전/전력"},
        {"종목":"한화에어로스페이스","티커":"012450.KS","테마":"방산"},
        {"종목":"현대로템","티커":"064350.KS","테마":"방산"},
        {"종목":"한국항공우주","티커":"047810.KS","테마":"방산"},
        {"종목":"LIG넥스원","티커":"079550.KS","테마":"방산"},
        {"종목":"레인보우로보틱스","티커":"277810.KQ","테마":"로봇"},
        {"종목":"두산로보틱스","티커":"454910.KS","테마":"로봇"},
        {"종목":"로보티즈","티커":"108490.KQ","테마":"로봇"},
        {"종목":"알테오젠","티커":"196170.KQ","테마":"바이오"},
        {"종목":"셀트리온","티커":"068270.KS","테마":"바이오"},
        {"종목":"삼성바이오로직스","티커":"207940.KS","테마":"바이오"},
        {"종목":"LG에너지솔루션","티커":"373220.KS","테마":"2차전지"},
        {"종목":"삼성SDI","티커":"006400.KS","테마":"2차전지"},
        {"종목":"에코프로비엠","티커":"247540.KQ","테마":"2차전지"},
        {"종목":"현대차","티커":"005380.KS","테마":"자동차"},
        {"종목":"기아","티커":"000270.KS","테마":"자동차"},
        {"종목":"KB금융","티커":"105560.KS","테마":"금융"},
        {"종목":"신한지주","티커":"055550.KS","테마":"금융"},
        {"종목":"하나금융지주","티커":"086790.KS","테마":"금융"},
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
        {"종목":"Alphabet","티커":"GOOGL","테마":"AI/검색"},
        {"종목":"Oracle","티커":"ORCL","테마":"클라우드"},
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
        {"종목":"Keyence","티커":"6861.T","테마":"자동화"},
        {"종목":"Nintendo","티커":"7974.T","테마":"콘텐츠"},
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

GUDO_NAMES = [
    "삼성전자","SK하이닉스","한미반도체","이수페타시스","오픈엣지테크놀로지",
    "HD현대일렉트릭","효성중공업","LS ELECTRIC","한화에어로스페이스",
    "현대로템","레인보우로보틱스","두산로보틱스"
]

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
        return open_markets[0][0], open_markets
    return "미국", open_markets

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
        turnover = last * volume_today

        return {
            "현재가": last,
            "등락률": change_pct,
            "거래량": volume_today,
            "거래량비율": vol_ratio,
            "거래대금": turnover,
            "상태": "자동",
        }
    except Exception:
        return None

def calc_score(change, vol_ratio, turnover):
    price_score = min(25, abs(change) * 4)
    volume_score = min(30, vol_ratio * 13)
    turnover_score = min(35, (turnover / 100_000_000_000) * 8)  # 약 1000억당 8점
    direction_bonus = 10 if change > 0 else 0
    return int(max(0, min(100, price_score + volume_score + turnover_score + direction_bonus)))

def calc_market(market):
    rows = []
    for s in UNIVERSE[market]:
        live = fetch_price(s["티커"])
        if live:
            score = calc_score(live["등락률"], live["거래량비율"], live["거래대금"])
            stage = "관심 급증" if score >= 80 else "관심 상승" if score >= 60 else "관찰" if score >= 35 else "약함"
            rows.append({**s, **live, "관심도점수": score, "단계": stage})
        else:
            rows.append({**s, "현재가": None, "등락률": 0.0, "거래량": 0.0, "거래량비율": 0.0, "거래대금": 0.0, "상태": "대기", "관심도점수": 0, "단계": "대기"})
    return pd.DataFrame(rows)

def get_index(market):
    idx = MARKET_INDEXES[market]
    live = fetch_price(idx["티커"])
    if live:
        return idx["지수"], live["현재가"], live["등락률"]
    return idx["지수"], None, 0.0

def display_df(df):
    view = df.copy()
    view["현재가"] = view["현재가"].apply(lambda x: "-" if pd.isna(x) else f"{x:,.2f}")
    view["등락률"] = view["등락률"].apply(lambda x: f"{x:+.2f}%")
    view["거래량비율"] = view["거래량비율"].apply(lambda x: f"{x:.1f}배")
    view["거래대금"] = view["거래대금"].apply(lambda x: f"{x/100_000_000:,.0f}억")
    return view

def render_market(market):
    idx_name, idx_val, idx_chg = get_index(market)
    c1, c2, c3 = st.columns(3)
    c1.metric(f"{MARKET_HOURS[market]['emoji']} {idx_name}", "-" if idx_val is None else f"{idx_val:,.2f}", f"{idx_chg:+.2f}%")
    c2.metric("업데이트", datetime.now(ZoneInfo("Asia/Seoul")).strftime("%H:%M:%S"))
    c3.metric("종목 수", len(UNIVERSE[market]))

    data = calc_market(market)
    top10 = data.sort_values(["관심도점수","거래대금","거래량비율"], ascending=False).head(10)
    turnover_top = data.sort_values("거래대금", ascending=False).head(10)
    volume_top = data.sort_values("거래량비율", ascending=False).head(10)
    up_top = data.sort_values("등락률", ascending=False).head(10)
    down_top = data.sort_values("등락률", ascending=True).head(10)

    sub1, sub2, sub3, sub4, sub5 = st.tabs(["🔥 관심 TOP10", "💰 거래대금", "📊 거래량 급증", "📈 상승률", "📉 하락률"])
    with sub1:
        cols = st.columns(5)
        for i, r in top10.head(5).reset_index(drop=True).iterrows():
            with cols[i]:
                st.metric(f"{i+1}. {r['종목']}", f"{int(r['관심도점수'])}점", f"{r['등락률']:+.2f}%")
                st.caption(f"{r['테마']} · {r['거래대금']/100_000_000:,.0f}억 · {r['거래량비율']:.1f}배")
        st.dataframe(display_df(top10), use_container_width=True, hide_index=True)
    with sub2:
        st.dataframe(display_df(turnover_top), use_container_width=True, hide_index=True)
    with sub3:
        st.dataframe(display_df(volume_top), use_container_width=True, hide_index=True)
    with sub4:
        st.dataframe(display_df(up_top), use_container_width=True, hide_index=True)
    with sub5:
        st.dataframe(display_df(down_top), use_container_width=True, hide_index=True)

    return data

current_market, open_markets = active_market()
now_kst = datetime.now(ZoneInfo("Asia/Seoul"))
open_text = ", ".join([f"{MARKET_HOURS[m]['emoji']} {m}" for m, _ in open_markets]) if open_markets else "현재 정규장 열림 없음"

st.info(f"현재 활성 시장: {MARKET_HOURS[current_market]['emoji']} **{current_market}** · 열린 시장: {open_text} · KST {now_kst.strftime('%H:%M:%S')}")

tab_home, tab_kr, tab_us, tab_jp, tab_tw, tab_supply, tab_gudo, tab_tao = st.tabs([
    "🏠 홈", "🇰🇷 한국", "🇺🇸 미국", "🇯🇵 일본", "🇹🇼 대만", "🏦 수급", "🧠 구도 후보", "🎯 TAO 시그널"
])

with tab_home:
    st.subheader(f"{MARKET_HOURS[current_market]['emoji']} 활성 시장 레이더")
    active_data = render_market(current_market)

with tab_kr:
    st.subheader("한국 시장")
    kr_data = render_market("한국")

with tab_us:
    st.subheader("미국 시장")
    us_data = render_market("미국")

with tab_jp:
    st.subheader("일본 시장")
    jp_data = render_market("일본")

with tab_tw:
    st.subheader("대만 시장")
    tw_data = render_market("대만")

with tab_supply:
    st.subheader("🏦 기관/외국인/개인 수급")
    st.warning("실시간 기관/외국인/개인 순매수는 무료 공개 데이터로 안정 제공이 어렵습니다.")
    st.markdown("""
    현재 버전에서는 **실시간 대체 지표**를 사용합니다.

    - 거래대금 TOP10
    - 거래량 급증 TOP10
    - 상승률/하락률 TOP10

    향후 장마감 후 데이터로:
    - 외국인 순매수
    - 기관 순매수
    - 개인 순매수  
    를 추가할 예정입니다.
    """)
    st.info("즉, 장중에는 거래대금과 거래량 급증을 '돈이 몰리는 흔적'으로 보고, 장마감 후 실제 수급 데이터로 검증하는 구조가 가장 현실적입니다.")

with tab_gudo:
    st.subheader("🧠 구도 후보")
    kr_all = calc_market("한국")
    gd = kr_all[kr_all["종목"].isin(GUDO_NAMES)].sort_values(["관심도점수","거래대금"], ascending=False)
    st.dataframe(display_df(gd), use_container_width=True, hide_index=True)
    avg = 0 if gd.empty else gd["관심도점수"].mean()
    st.metric("구도 후보 평균 관심도", f"{avg:.0f}점")

with tab_tao:
    st.subheader("🎯 TAO 시그널")
    kr_all = calc_market("한국")
    us_all = calc_market("미국")
    tw_all = calc_market("대만")

    kr_score = kr_all["관심도점수"].head(8).mean() if not kr_all.empty else 0
    us_score = us_all["관심도점수"].head(8).mean() if not us_all.empty else 0
    tw_score = tw_all["관심도점수"].head(8).mean() if not tw_all.empty else 0
    gudo_score = kr_all[kr_all["종목"].isin(GUDO_NAMES)]["관심도점수"].mean()

    if pd.isna(gudo_score):
        gudo_score = 0

    tao_signal = int(max(0, min(100, kr_score*0.35 + us_score*0.25 + tw_score*0.15 + gudo_score*0.25)))

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("한국", f"{kr_score:.0f}")
    c2.metric("미국", f"{us_score:.0f}")
    c3.metric("대만", f"{tw_score:.0f}")
    c4.metric("구도 후보", f"{gudo_score:.0f}")
    c5.metric("TAO 종합", f"{tao_signal}점")

    if tao_signal >= 80:
        st.success("TAO 관점에서 시장 관심도와 핵심 후보 신호가 강한 구간입니다.")
    elif tao_signal >= 60:
        st.info("TAO 관점에서 관심도가 살아있는 구간입니다.")
    elif tao_signal >= 40:
        st.warning("TAO 관점에서 방향성 확인이 필요한 구간입니다.")
    else:
        st.error("TAO 관점에서 관심도 신호가 약한 구간입니다.")

st.caption("태형레이더는 투자 자문이 아니라 시장 관심도와 구도 스타일 후보를 탐색하는 개인용 분석 도구입니다.")
