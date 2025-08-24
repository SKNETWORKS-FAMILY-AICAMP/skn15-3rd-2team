from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
    
class AgentState(TypedDict):
    con_current : Annotated[list, add_messages]
    context_current : Annotated[list, add_messages]
    tmp_input : str
    todo_list : list
    # 유저 정보---------------------------
    empty_info : list   # 아직 없는 정보의 키

    education : list
    major : list
    career : list
    licenses : Annotated[list, add_messages]
    prefer_condition : Annotated[list, add_messages]
    main_experience : Annotated[list, add_messages]

    pre_salary : int
    pre_location : Annotated[list, add_messages]
    pre_industry : Annotated[list, add_messages]
    pre_role : Annotated[list, add_messages]
    pre_company_type : Annotated[list, add_messages]
    pre_employee_type : Annotated[list, add_messages]
    pre_request : Annotated[list, add_messages]

    keywords : list
    # --------------------------
    jasosu_main : str
    jasosu_com_dict : dict

def state_init() -> dict:
    initial_state = {
        "con_current": [],
        "context_current": [],
        "tmp_input": "",
        "todo_list": [],
        # 유저정보-- 
        "empty_info" : [],
        "education": [],
        "major": [],
        "career": [],
        "licenses": [],
        "prefer_condition": [],
        "main_experience": [],
        "pre_salary": [0],
        "pre_location": [],
        "pre_industry": [],
        "pre_role": [],
        "pre_company_type": [],
        "pre_employee_type": [],
        "pre_request": [],
        "keywords": [],

        # ----
        "jasosu_main": "",
        "jasosu_com_dict": {},
        }
    return initial_state



