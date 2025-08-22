import chainlit as cl
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from transformers import pipeline
from typing import cast
from state_types import AgentState

from utils.cover_letter import cover_letter_feedback
from utils.job_search import search_jobs

classifier = pipeline("zero-shot-classification", model="joeddav/xlm-roberta-large-xnli")

async def handle_input_with_state(state: AgentState) -> str:
    user_input = state["ctx"]["tmp_prompt"]
    intent = classify_user_input(user_input)
    state["ctx"]["intent"] = intent  # 🔥 분류 결과를 상태에 반영

    # 최근 대화 일부를 문맥으로 활용
    recent_context = "\n".join(state["ctx"].get("con_past", [])[-3:])  # 최근 3개만

    if (intent == "자기소개서 작성") or (intent == "자기소개서 첨삭"):
        prompt_with_context = f"이전 내용:\n{recent_context}\n\n현재 질문:\n{user_input}"
        return await cover_letter_feedback(prompt_with_context)
    elif intent == "모집공고 탐색":
        return search_jobs(user_input)
    else:
        return "자기소개서 OR 모집공고 관련 내용을 입력해주시면 도움을 드릴 수 있습니다."

def classify_user_input(text: str) -> str:
    # candidate_labels = ["자소서", "모집공고", "기타"]
    candidate_labels = [
        "자기소개서 작성",
        "자기소개서 첨삭",
        "모집공고 탐색",
        "기타"
    ]
    
    # result = classifier(text, candidate_labels)
    result = classifier(
        text,
        candidate_labels,
        hypothesis_template="이 문장은 {} 요청과 관련이 있다."
    )
    top_label = result["labels"][0]
    return top_label

# def route_user_input(user_input: str) -> str:
#     if contains_resume_keywords(user_input):
#         return "resume_handler"
#     elif contains_job_posting_keywords(user_input):
#         return "job_posting_handler"
#     else:
#         return "default_handler"

# def contains_resume_keywords(text: str) -> bool:
#     keywords = ['자소서', '자기소개서', '첨삭', '수정', '작성', '피드백', '자기소개', '지원동기', '강점', '약점']
#     return any(keyword in text.lower() for keyword in keywords)

# def contains_job_posting_keywords(text: str) -> bool:
#     keywords = ['모집공고', '채용공고', '공고', '지원자격', '우대사항', '전형절차', '회사 정보', '포지션', '직무']
#     return any(keyword in text.lower() for keyword in keywords)

# async def handle_input(user_input: str) -> str:
#     route = route_user_input(user_input)
#     if route == "resume_handler":
#         return await cover_letter_feedback(user_input)
#     elif route == "job_posting_handler":
#         return search_jobs(user_input)
#     else:
#         return "자기소개서 OR 모집공고 관련 내용을 입력해주시면 도움을 드릴 수 있습니다."

@cl.on_chat_start
async def start():
    await cl.Message(content="💼 **JobPal - 당신의 AI 취업 도우미** 🤖\n\n무엇을 도와드릴까요? 자소서 또는 공고와 관련된 내용을 입력해 주세요.").send()

@cl.on_message
async def main(message: cl.Message):
    user_input = message.content.strip()

    # 기존 세션 상태 가져오기 (없으면 초기화)
    state = cl.user_session.get("agent_state")
    if state is None:
        state = {
            "ctx": {
                "tmp_prompt": user_input,
                "intent": "",
                "con_past": [],
                "con_current": [],
                "context_past": "",
                "context_current": "",
                "tmp_req": [],
                "todo_list": [],
            },
            "user_info": {
                "education": [],
                "major": [],
                "career": [],
                "licenses": [],
                "main_experience": [],
                "pre_location": [],
                "pre_role": [],
                "pre_industry": [],
                "pre_company_type": [],
                "pre_employee_type": [],
                "pre_request": [],
                "keywords": [],
                "job_sufficiency": 0.0,
                "jasosu_job_sufficiency": 0.0,
            },
            "jasosu": {
                "jasosu_main": "",
                "jasosu_com_dict": {}
            }
        }

    # 사용자 입력 반영
    state["ctx"]["tmp_prompt"] = user_input

    msg = await cl.Message(content="⏳ 잠시만 기다려 주세요...").send()

    try:
        response_output = await handle_input_with_state(state)
    except Exception as e:
        response_output = f"오류가 발생했습니다: {str(e)}"

     # 대화 이력 저장
    state["ctx"]["con_past"].append(user_input)
    state["ctx"]["con_current"].append(response_output)

    # 세션은 저장은 대화 저장 이후
    cl.user_session.set("agent_state", state)

    # 의도도 함께 출력해보자 (디버깅용) 의도 문구는 나중에는 지워야함
    intent = state["ctx"].get("intent", "")
    # await cl.Message(content=f"[의도: {intent}] {response_output}").send()
    msg.content = f"[의도: {intent}] {response_output}"
    await msg.update()
