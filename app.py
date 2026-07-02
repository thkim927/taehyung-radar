  import streamlit as st
import pandas as pd

st.set_page_config(page_title="태형레이더", page_icon="📡", layout="wide")

st.title("📡 태형레이더 v1.1")
st.caption("한국·미국·일본·대만 증시와 구도 TAO 분석을 위한 첫 번째 대시보드")

st.divider()

st.header("🌏 오늘 글로벌 시장 레이더")

market_data = [
    {"지역": "한국", "지수": "KOSPI", "중요도": "★★★★★", "태형레이더 관점": "TAO 직접 영향 가능성 높음"},
    {"지역": "한국", "지수": "KOSDAQ", "중요도": "★★★☆☆", "태형레이더 관점": "중소형 성장주/벤처 심리 확인"},
    {"지역": "미국", "지수": "NASDAQ", "중요도": "★★★★★", "태형레이더 관점": "AI·반도체 선행 신호"},
    {"지역": "미국", "지수": "SOX 반도체", "중요도": "★★★★★", "태형레이더 관점": "SK하이닉스·삼성전자 영향 추정 핵심"},
    {"지역": "일본", "지수": "Nikkei 225", "중요도": "★★★★☆", "태형레이더 관점": "글로벌 위험선호·반도체 장비주 심리"},
    {"지역": "일본", "지수": "TOPIX", "중요도": "★★★☆☆", "태형레이더 관점": "일본 전체 증시 방향 확인"},
    {"지역": "대만", "지수": "TAIEX", "중요도": "★★★★★", "태형레이더 관점": "TSMC·AI 반도체 밸류체인 핵심"},
    {"지역": "대만", "지수": "TSMC", "중요도": "★★★★★", "태형레이더 관점": "글로벌 AI/HBM 투자심리 핵심"},
]

df = pd.DataFrame(market_data)

cols = st.columns(4)
for i, row in df.iterrows():
    with cols[i % 4]:
        st.metric(label=f"{row['지역']} · {row['지수']}", value=row["중요도"])
        st.caption(row["태형레이더 관점"])

st.divider()

st.header("📊 시장 영향도 요약")
st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()

st.header("🧠 구도 TAO 분석 준비")
st.info("다음 버전에서 기준가, 설정원본액, 순자산, 주식편입비를 입력하면 TAO 변동률과 예상 영향도를 계산합니다.")

st.subheader("입력 예정 항목")
st.write("- 기준가")
st.write("- 설정원본액")
st.write("- 순자산")
st.write("- 주식 편입비")
st.write("- 분기보고서 기준 롱/숏 비중")

st.divider()

st.header("🚀 다음 업그레이드")
st.write("v1.2 : TAO 기준가 입력 화면")
st.write("v1.3 : 기준가 변동률 자동 계산")
st.write("v1.4 : 일본·대만·미국 반도체 영향도 반영")
st.write("v2.0 : 구도 AI 1차 모델")
