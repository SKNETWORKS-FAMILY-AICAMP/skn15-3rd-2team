# state_types.py
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class ContextState(TypedDict):
    con_past : Annotated[list, add_messages]
    con_current : Annotated[list, add_messages]
    context_past : str
    context_current : str
    tmp_prompt : str
    tmp_req : list
    todo_list : list
    intent: str  # 사용자 의도 분류 결과

class UserState(TypedDict):
    education : list
    major : list
    career : list
    licenses : list
    main_experience : list

    pre_location : list
    pre_role : list
    pre_industry : list
    pre_company_type : list
    pre_employee_type : list
    pre_request : list

    keywords : list

    job_sufficiency : float
    jasosu_job_sufficiency : float

class JasosuState(TypedDict):
    jasosu_main : str
    jasosu_com_dict : dict

class AgentState(TypedDict):
    ctx : ContextState
    user_info : UserState
    jasosu : JasosuState
