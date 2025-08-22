from typing import Annotated, TypedDict
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

model = ChatOpenAI(model="gpt-4", temperature=0.7)

base_prompt = SystemMessage(
    "당신은 자기소개서를 작성하는 어시스턴트입니다. "
    "입력된 정보로 최고의 자기소개서를 생성하세요."
)

reflection_prompt = SystemMessage(
    "당신은 인사 담당자입니다. "
    "방금 작성된 자기소개서를 읽고 구체성과 설득력 위주로 피드백을 작성해주세요."
)

class State(TypedDict):
    messages: Annotated[list, add_messages]

def generate(state: State) -> State:
    answer = model.invoke([base_prompt] + state["messages"])
    return {"messages": [answer]}

def reflect(state: State) -> State:
    answer = model.invoke([reflection_prompt] + state["messages"])
    return {"messages": [answer]}

def cover_letter_feedback(user_input: str) -> str:
    state = {"messages": [HumanMessage(content=user_input)]}

    builder = StateGraph(State)
    builder.add_node("generate", generate)
    builder.add_node("reflect", reflect)
    builder.set_entry_point("generate")
    builder.add_edge("generate", "reflect")
    builder.set_finish_point("reflect")

    graph = builder.compile()
    result = graph.invoke(state)
    return result["messages"][-1].content
