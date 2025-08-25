import pandas as pd
import json
import re
from typing import Annotated, TypedDict
from sqlalchemy import create_engine, text
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages


def company_ideal_talent_api(model: ChatOpenAI, company_name: str, lang: str = 'ko') -> dict:
    if lang == 'ko':
        query = (
            f"'{company_name}' 회사의 인재상과 핵심 가치·문화를 JSON 형식으로 세 항목으로 요약해 주세요. "
            "출력 예시: "
            "{\"회사명\": \"삼성전자\", \"인재상_키워드\": [\"도전\", \"창의\", \"협력\"], \"요약\": \"혁신을 주도하는 인재\"}"
        )
    elif lang == 'en':
        query = (
            f"Please summarize the ideal talent and core values of '{company_name}' company in JSON format with three items. "
            "Example format: "
            "{\"CompanyName\": \"Samsung Electronics\", \"KeyQualities\": [\"Challenge\", \"Creativity\", \"Collaboration\"], \"Summary\": \"Talent leading innovation\"}"
        )
    else:
        query = (
            f"Please provide the ideal talent description of '{company_name}' in {lang} in JSON format."
        )
    response = model.invoke([HumanMessage(content=query)]).content
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return {
            "회사명" if lang == 'ko' else "CompanyName": company_name,
            "인재상_키워드" if lang == 'ko' else "KeyQualities": ["자동추출"],
            "요약" if lang == 'ko' else "Summary": response.strip()
        }


def upsert_ideal_to_db(engine, company_name, keywords, summary, language='ko'):
    insert_query = text("""
        INSERT INTO ideal_table (회사, 인재상_키워드, 요약, language)
        VALUES (:company, :keyword, :summary, :language)
        ON CONFLICT (회사, language) DO UPDATE
        SET 인재상_키워드 = EXCLUDED.인재상_키워드,
            요약 = EXCLUDED.요약
    """)
    with engine.connect() as conn:
        conn.execute(insert_query, {
            'company': company_name,
            'keyword': ",".join(keywords) if isinstance(keywords, list) else str(keywords),
            'summary': summary,
            'language': language
        })
        conn.commit()


class State(TypedDict):
    messages: Annotated[list, add_messages]


model = ChatOpenAI(model="gpt-5-2025-08-07")


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
            if example_resume.get("q"):
                parts.append(f"자소서 문항:\n{example_resume['q']}")
            if example_resume.get("a"):
                parts.append(f"예시 답변:\n{example_resume['a']}")
            if example_resume.get("advice"):
                parts.append(f"추가 조언:\n{example_resume['advice']}")
        else:
            parts.append(str(example_resume))
    if char_limit > 0:
        parts.append(
            f"\n자기소개서는 글자 수 최대 {char_limit}자이며, 가능한 한 {int(char_limit * 0.9)}자 이상으로 작성하세요."
        )
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
    latest_letter = None
    for msg in reversed(state["messages"]):
        if isinstance(msg, AIMessage):
            latest_letter = msg.content
            break

    latest_feedback = None
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            latest_feedback = msg.content
            break

    if not latest_letter or not latest_feedback:
        answer = model.invoke([reflection_prompt] + state["messages"])
        return {"messages": [HumanMessage(content=answer.content)]}

    feedback_prompt_text = (
        "아래는 지금까지 작성된 자기소개서입니다:\n"
        f"{latest_letter}\n\n"
        "아래는 지원자가 요청한 수정/변경사항입니다:\n"
        f"{latest_feedback}\n\n"
        "최대한 글자 수 제한 내에서 글자 수를 늘려 내용을 충실하고 구체적으로 수정해 주세요."
    )
    feedback_prompt = SystemMessage(feedback_prompt_text)
    answer = model.invoke([feedback_prompt])
    return {"messages": [AIMessage(content=answer.content)]}


def pretty_print(text: str):
    sentences = re.split(r'(?<=[\.。!！\?？])\s+', text.strip())
    formatted = "\n\n".join(sentences)
    print(formatted)


def run_interactive_resume():
    db_connection_url = 'postgresql+psycopg2://play:123@192.168.0.8:5432/team2'
    engine = create_engine(db_connection_url)

    try:
        df_ideal = pd.read_sql("SELECT 회사, 인재상_키워드, 요약, language FROM ideal_table", engine)
    except Exception as e:
        print(f"내부 인재상 DB 로드 오류: {e}")
        df_ideal = pd.DataFrame()

    try:
        df_resume = pd.read_sql("SELECT company, position, q, a, advice FROM merged_resume", engine)
    except Exception as e:
        print(f"자소서 예시 DB 로드 오류: {e}")
        df_resume = pd.DataFrame()

    user_company = input("지원 회사명을 입력하세요 (예: 삼성전자): ").strip()
    user_job = input("지원 직무를 입력하세요 (예: 일반사무직): ").strip()
    user_spec = input("본인의 대외 스펙/경험을 입력하세요 (예: 토익900, 컴활1급 등): ").strip()

    user_char_limit = 0
    try:
        user_char_limit = int(input("자기소개서 글자 수 제한을 입력하세요 (예: 500, 제한 없으면 0): ").strip())
    except ValueError:
        print("잘못된 입력입니다. 글자 수 제한을 적용하지 않습니다.")

    user_language = input("지원 회사의 인재상 언어를 입력하세요 (ko=한국어, en=영어 등): ").strip().lower()
    if user_language not in ['ko', 'en']:
        user_language = 'ko'

    base_generate_prompt, reflection_prompt = get_prompts(user_language)

    filtered_ideal = df_ideal[
        (df_ideal['회사'].astype(str).str.contains(user_company, case=False, na=False)) &
        (df_ideal['language'] == user_language)
    ]
    company_culture = None
    if not filtered_ideal.empty:
        keyword = filtered_ideal.iloc[0]['인재상_키워드']
        summary = filtered_ideal.iloc[0]['요약']
        company_culture = f"인재상 키워드: {keyword}\n요약: {summary}"
        print(f"\n내부 DB에서 '{user_company}' ({user_language}) 인재상 정보를 찾았습니다.\n")
    else:
        print(f"\n내부 DB에 '{user_company}' ({user_language}) 인재상 정보가 없어 API 조회를 시도합니다...")
        api_result = company_ideal_talent_api(model, user_company, lang=user_language)
        if user_language == 'ko':
            company_name = api_result.get("회사명", user_company)
            keywords = api_result.get("인재상_키워드", [])
            summary = api_result.get("요약", "")
        else:
            company_name = api_result.get("CompanyName", user_company)
            keywords = api_result.get("KeyQualities", [])
            summary = api_result.get("Summary", "")

        company_culture = f"인재상 키워드: {', '.join(keywords)}\n요약: {summary}"
        try:
            upsert_ideal_to_db(engine, company_name, keywords, summary, language=user_language)
            print(f"API로 조회한 인재상 정보를 DB에 저장했습니다.\n")
        except Exception as e:
            print(f"인재상 정보 DB 저장 중 오류 발생: {e}")

    filtered_resume = df_resume[
        (df_resume['company'].str.strip() == user_company) &
        (df_resume['position'].str.contains(user_job, case=False, na=False))
    ]

    q_list = filtered_resume['q'].dropna().unique().tolist() if not filtered_resume.empty else []
    if not q_list:
        if user_language == 'en':
            q_list = [
                "Introduction and motivation",
                "Key experience and skills",
                "Fit with company and role",
                "Background and strengths",
                "Goals and aspirations"
            ]
        else:
            q_list = [
                "자기소개 (대인관계, 장단점, 성장과정 등)",
                "지원동기 및 입사 후 포부",
                "본인의 강점 및 역량",
                "위기극복 사례",
                "주도적으로 업무 수행한 경험"
            ]

    print(f"\n작성할 자소서 문항이 다음과 같이 있습니다:")
    for i, question in enumerate(q_list, 1):
        print(f"{i}. {question}")

    selected_idx = input("어떤 문항에 대한 자소서를 작성하시겠습니까? 번호를 입력하세요 (예: 1): ").strip()

    example_resume = None
    user_custom_q = None
    try:
        selected_idx = int(selected_idx)
        if 1 <= selected_idx <= len(q_list):
            selected_q = q_list[selected_idx - 1]
            if not filtered_resume.empty and selected_q in filtered_resume['q'].values:
                chosen_row = filtered_resume[filtered_resume['q'] == selected_q].iloc[0]
                example_resume = {
                    "q": selected_q,
                    "a": chosen_row.get('a', ''),
                    "advice": chosen_row.get('advice', '')
                }
        else:
            user_custom_q = input("목록에 없는 문항입니다. 직접 작성할 자기소개서 문항을 입력해주세요:\n").strip()
    except Exception:
        user_custom_q = input("번호 입력이 잘못되었습니다. 작성할 자기소개서 문항을 입력해주세요:\n").strip()

    if user_custom_q:
        print(f"\n입력하신 문항에 대해 자기소개서를 생성합니다: {user_custom_q}")
        example_resume = {"q": user_custom_q, "a": "", "advice": ""}

    generate_prompt = make_job_prompt(
        base_generate_prompt,
        company_culture=company_culture,
        example_resume=example_resume,
        char_limit=user_char_limit
    )

    state = {
        "messages": [
            HumanMessage(content=f"지원 회사: {user_company}\n지원 직무: {user_job}\n스펙 및 경험: {user_spec}")
        ]
    }

    builder = StateGraph(State)
    builder.add_node("generate", lambda s: generate(s, generate_prompt, user_char_limit))
    builder.add_node("reflect", lambda s: reflect(s, reflection_prompt))
    builder.add_edge(START, "generate")
    builder.add_edge("reflect", "generate")
    graph = builder.compile()

    final_resume = None
    reflection_content = None

    while True:
        outputs = graph.stream(state)
        for output in outputs:
            node, val = list(output.items())[0]
            content = val["messages"][-1].content

            if user_char_limit > 0 and len(content) > user_char_limit:
                print(f"\n⚠️ 생성된 자기소개서가 {user_char_limit}자를 초과했습니다.\n")

            print(f"\n=== {node.upper()} 단계 ===\n")
            pretty_print(content)
            print("\n")

            state["messages"].append(val["messages"][-1])

            if node == "generate":
                final_resume = content
            elif node == "reflect":
                reflection_content = content

        if reflection_content:
            print(f"===== 첨삭 피드백 =====\n")
            pretty_print(reflection_content)
            print("\n")

        user_edit = input("수정하고 싶은 부분이나 요청사항을 입력하세요 (수정 완료 시 '완료' 입력): ").strip()

        if user_edit.lower() == "완료":
            print("\n✅ 최종 자기소개서:\n")
            pretty_print(final_resume)
            break

        state["messages"].append(HumanMessage(content=user_edit))


if __name__ == "__main__":
    run_interactive_resume()
