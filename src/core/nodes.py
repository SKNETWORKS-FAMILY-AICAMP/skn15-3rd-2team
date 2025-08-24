from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from utils.utils import TODO_CATEGORIES, USER_INFO

from .state import AgentState

from .utils import prompts
from .utils import parsers
from .utils import utils

# llm_base = ChatOpenAI(model="gpt-5", temperature=0)
# llm_think = ChatOpenAI(model="gpt-5", temperature=0)
llm_nano = ChatOpenAI(model="gpt-5-nano", temperature=0)

# 요구사항 추출
parser_request = PydanticOutputParser(pydantic_object=parsers.GetRequests)
prompt_request = ChatPromptTemplate.from_template(
    template=prompts.pt_requests,
    partial_variables={"format_instructions": parser_request.get_format_instructions()},
)
chain_requests = prompt_request | llm_nano | parser_request

# 정보 추출
parser_info = PydanticOutputParser(pydantic_object=parsers.GetInfo)
prompt_info = ChatPromptTemplate.from_template(
    template=prompts.pt_info,
    partial_variables={"format_instructions": parser_info.get_format_instructions()},
)
chain_info = prompt_info | llm_nano | parser_info

# 희망사항 추출
parser_prefer = PydanticOutputParser(pydantic_object=parsers.GetPrefer)
prompt_prefer = ChatPromptTemplate.from_template(
    template=prompts.pt_prefer,
    partial_variables={"format_instructions": parser_prefer.get_format_instructions()},
)
chain_prefer = prompt_prefer | llm_nano | parser_prefer


# 할일정리, 정보 추출
def initNode(state: AgentState):
    # 사전작업
    tmp_input = state.get('tmp_input')
    context_current = state.get('context_current')
    # 요구사항 정리
    todo_list = chain_requests.invoke({"input1": tmp_input})
    # 정보 파악
    info = chain_info.invoke({"input1": tmp_input})
    # 희망사항 파악
    prefer = chain_prefer.invoke({"input1": tmp_input})
    
    todo_list = [(i.task.value, i.message)for i in todo_list.requests]
    info = {key: utils.convert_enum_to_string(value) for key, value in info.model_dump().items()}
    prefer = {key: utils.convert_enum_to_string(value) for key, value in prefer.model_dump().items()}

    final_dict = {'todo_list':todo_list, **info, **prefer}
    final_dict = {key: value for key, value in final_dict.items() if value}
    return final_dict

def managerNode(state: AgentState):
    return {}

def gujicNode(state: AgentState):
    # 정보 부족하면 필요한 정보 요청
    empty_info = []
    for info in USER_INFO:
        if not info:
            empty_info.append(info)

    if len(empty_info) > 8:
        return {"empty_info" : empty_info}
    
    # 정보 충분하면 사람인 검색
    

    # 나온 정보 저장

    pass

def elseNode(state: AgentState):
    pass


def jasosuMainNode(state: AgentState):
    pass

def outputNode(state: AgentState):
    pass