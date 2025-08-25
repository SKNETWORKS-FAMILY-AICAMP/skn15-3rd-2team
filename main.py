import streamlit as st
import pandas as pd
import json
import re
import asyncio
from typing import Annotated, TypedDict
from sqlalchemy import create_engine, text

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph.message import add_messages

# ===== CLI 함수들을 동일 모듈 내에 통합 =====
# (원래 cli.py의 주요 함수들)

from jobkorea_cli.models import Spec
from jobkorea_cli.llm import parse_spec, ask_required_batch, map_filters
from jobkorea_cli.cli import crawl_by_roles_multi

def _missing_required(s: Spec) -> list[str]:
    m = []
    if not (s.career and s.career.level): m.append("career.level")
    if not s.location: m.append("location")
    if not s.employment_type: m.append("employment_type")
    if not s.education: m.append("education")
    return m

async def _interactive_spec() -> Spec:
    print("예) 서울 거주 신입, 4년제 졸, 파이썬/SQL 가능, 정보처리기사 보유, 통계학 전공")
    user_text = input("입력> ").strip()
    spec = await parse_spec(user_text)
    miss = _missing_required(spec)
    if miss:
        print("[필수 정보 확인중 ...]")
        turns = await ask_required_batch(spec, miss)
        for t in turns:
            ask = getattr(t, "ask", "") or "값을 입력해 주세요."
            options = getattr(t, "options", []) or []
            field = getattr(t, "field", None)
            print(ask)
            if options:
                print("선택지:", ", ".join(options))
            ans = input("답변> ").strip()
            if not ans:
                continue
            if field == "career.level":
                spec.career.level = ans
            elif field == "location":
                spec.location = ans
            elif field == "employment_type":
                spec.employment_type = ans
            elif field == "education":
                spec.education = ans
            elif field == "skills":
                spec.skills = [s.strip() for s in ans.split(",") if s.strip()]
            elif field == "certifications":
                spec.certifications = [s.strip() for s in ans.split(",") if s.strip()]
            elif field == "major":
                spec.major = ans
    return spec

async def main_cli():
    print("=== 잡코리아 역할별 빠른 서치 (expanded_roles 기반) ===")
    print("종료: exit/quit\n")
    spec = await _interactive_spec()
    applied = await map_filters(spec)
    print("\n[적용된 키워드]")
    print("- expanded_roles:", applied.get("expanded_roles") or [])
    print("- keywords:", applied.get("keywords") or [])
    expanded_roles = applied.get("expanded_roles") or []
    if not expanded_roles:
        print("\n[결과] expanded_roles가 비어 있습니다. 입력 문장을 더 구체적으로 써 주세요.")
        return
    grouped = await crawl_by_roles_multi(expanded_roles, per_role=2)
    any_hit = False
    print("\n[역할별 Top 2]")
    for role_kw in expanded_roles:
        docs = grouped.get(role_kw, [])
        print(f"\n▶ {role_kw}")
        if not docs:
            print(" - (결과 없음)")
            continue
        any_hit = True
        for d in docs:
            print(f" - {d.title if d.title else '(제목 없음)'}")
            print(f" 링크: {d.url}")
    if not any_hit:
        print("\n(모든 역할에서 결과 없음)")

# ===== streamlit.py 부분 =====

# LLM 모델 연결
model = ChatOpenAI(model="gpt-5-2025-08-07")
DB_CONNECTION_URL = 'postgresql+psycopg2://play:123@192.168.0.8:5432/team2'
engine = create_engine(DB_CONNECTION_URL)

# 상태 정의
class State(TypedDict):
    messages: Annotated[list, add_messages]

# 기본 프롬프트
base_generate_prompt_ko = SystemMessage(
    "당신은 자기소개서를 작성하는 어시스턴트입니다. "
    "입력된 지원 직무와 본인 스펙, 경력, 경험 등을 토대로 최고의 자기소개서를 작성하세요."
)

base_generate_prompt_en = SystemMessage(
    "You are an assistant specialized in writing cover letters. "
    "Based on the given job position, personal qualifications, and experiences, write the best English cover letter."
)

reflection_prompt_ko = SystemMessage(
    "당신은 인사 담당자입니다. "
    "방금 생성된 자기소개서를 읽고 내용, 구체성, 설득력, 어투 등에서 개선이 필요한 부분을 상세하게 피드백하세요."
)

reflection_prompt_en = SystemMessage(
    "You are a hiring manager. "
    "Please review the cover letter and provide detailed feedback on content, concreteness, persuasiveness, and tone."
)

def get_prompts(language: str):
    if language == 'en':
        return base_generate_prompt_en, reflection_prompt_en
    else:
        return base_generate_prompt_ko, reflection_prompt_ko

def make_job_prompt(base_prompt, company_culture=None, example_resume=None, char_limit=0):
    parts = [base_prompt.content]
    if company_culture:
        parts.append(f"\n해당 회사의 인재상:\n{company_culture}")
    if example_resume:
        parts.append("\n내부 DB 자소서 예시 참고 내용:")
        if isinstance(example_resume, dict):
            if example_resume.get("q"): parts.append(f"자소서 문항:\n{example_resume['q']}")
            if example_resume.get("a"): parts.append(f"예시 답변:\n{example_resume['a']}")
            if example_resume.get("advice"): parts.append(f"추가 조언:\n{example_resume['advice']}")
        else:
            parts.append(str(example_resume))
    if char_limit > 0:
        parts.append(f"\n자기소개서는 글자 수 최대 {char_limit}자이며, 가능한 한 {int(char_limit * 0.9)}자 이상으로 작성하세요.")
    parts.append("\n위 정보를 참고하여 자기소개서를 작성하세요.")
    return SystemMessage('\n'.join(parts))

def generate(state: State, generate_prompt: SystemMessage, char_limit: int = 0) -> State:
    for _ in range(3):
        answer = model.invoke([generate_prompt] + state["messages"])
        content = answer.content
        if char_limit <= 0 or len(content) >= char_limit * 0.9:
            return {"messages": [answer]}
    return {"messages": [answer]}

def reflect(state: State, reflection_prompt: SystemMessage) -> State:
    answer = model.invoke([reflection_prompt] + state["messages"])
    return {"messages": [HumanMessage(content=answer.content)]}

def pretty_print(text: str) -> str:
    sentences = re.split(r'(?<=[\.。!！\?？])\s+', text.strip())
    return "\n\n".join(sentences)

def load_ideal_from_db(company, language):
    try:
        df = pd.read_sql("SELECT 회사, 인재상_키워드, 요약, language FROM ideal_table", engine)
        filtered = df[(df['회사'].astype(str).str.contains(company, case=False, na=False)) &
                      (df['language'] == language)]
        if not filtered.empty:
            keyword = filtered.iloc[0]['인재상_키워드']
            summary = filtered.iloc[0]['요약']
            return keyword, summary
    except Exception:
        return None, None
    return None, None

def load_resume_from_db(company, job):
    try:
        df = pd.read_sql("SELECT company, position, q, a, advice FROM merged_resume", engine)
        filtered = df[(df['company'].str.strip() == company) &
                      (df['position'].str.contains(job, case=False, na=False))]
        return filtered
    except Exception:
        return pd.DataFrame()

# ======== Streamlit UI ========

st.title("AI 자기소개서 작성 & 역할별 검색 통합 어시스턴트")

# --- 자기소개서 작성 UI ---

st.header("✍️ 자기소개서 작성 & 첨삭")
company = st.text_input("지원 회사명")
job = st.text_input("지원 직무")
spec = st.text_area("본인 스펙 및 경험 입력")
language = st.selectbox("언어 선택", ["ko", "en"])
char_limit = st.number_input("최대 글자 수 (0은 제한 없음)", min_value=0, step=10, value=0)
use_example = st.checkbox("내부 DB 자소서 예시 참고 사용")

# --- 사이드바: 역할별 채용검색 ---

st.sidebar.title("🔍 역할별 빠른 채용 검색")
user_text = st.sidebar.text_area("스펙 입력 (예: '서울 거주 신입, 4년제 졸, 파이썬 가능')")

if st.sidebar.button("검색 실행"):

    async def run_cli_side(user_text):
        spec = await parse_spec(user_text)
        applied = await map_filters(spec)
        expanded_roles = applied.get("expanded_roles") or []
        results = {}
        if expanded_roles:
            results = await crawl_by_roles_multi(expanded_roles, per_role=2)
        return applied, results

    applied, grouped = asyncio.run(run_cli_side(user_text))

    st.sidebar.write("### Expanded Roles")
    st.sidebar.write(applied.get("expanded_roles") or [])

    st.sidebar.write("### Keywords")
    st.sidebar.write(applied.get("keywords") or [])

    st.sidebar.markdown("---")

    st.sidebar.write("## 검색 결과")
    for role_kw in (applied.get("expanded_roles") or []):
        docs = grouped.get(role_kw, [])
        st.sidebar.subheader(f"▶ {role_kw}")
        if not docs:
            st.sidebar.write("- (결과 없음)")
            continue
        for d in docs:
            st.sidebar.markdown(f"**{d.title if d.title else '(제목 없음)'}**")
            st.sidebar.write(f"🔗 [링크]({d.url})")
            st.sidebar.markdown("---")
