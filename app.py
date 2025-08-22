import chainlit as cl
from utils.cover_letter import cover_letter_feedback
from utils.job_search import search_jobs

def route_user_input(user_input: str) -> str:
    if contains_resume_keywords(user_input):
        return "resume_handler"
    elif contains_job_posting_keywords(user_input):
        return "job_posting_handler"
    else:
        return "default_handler"

def contains_resume_keywords(text: str) -> bool:
    keywords = ['자소서', '자기소개서', '첨삭', '수정', '작성', '피드백', '자기소개', '지원동기', '강점', '약점']
    return any(keyword in text.lower() for keyword in keywords)

def contains_job_posting_keywords(text: str) -> bool:
    keywords = ['모집공고', '채용공고', '공고', '지원자격', '우대사항', '전형절차', '회사 정보', '포지션', '직무']
    return any(keyword in text.lower() for keyword in keywords)

def handle_input(user_input: str) -> str:
    route = route_user_input(user_input)
    if route == "resume_handler":
        return cover_letter_feedback(user_input)
    elif route == "job_posting_handler":
        return search_jobs(user_input)
    else:
        return "자기소개서 OR 모집공고 관련 내용을 입력해주시면 도움을 드릴 수 있습니다."

@cl.on_chat_start
async def start():
    await cl.Message(content="💼 **JobPal - 당신의 AI 취업 도우미** 🤖\n\n무엇을 도와드릴까요? 자소서 또는 공고와 관련된 내용을 입력해 주세요.").send()

@cl.on_message
async def main(message: cl.Message):
    user_input = message.content.strip()

    try:
        response_output = handle_input(user_input)
    except Exception as e:
        response_output = f"오류가 발생했습니다: {str(e)}"

    await cl.Message(content=response_output).send()
