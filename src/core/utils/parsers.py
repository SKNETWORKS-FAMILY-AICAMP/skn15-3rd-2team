from pydantic import BaseModel, Field
from typing import List, Literal
from enum import Enum
from . import enums
from utils.utils import TODO_CATEGORIES

# 할일 정리
class TaskCategory(str, Enum):
    GUJIC = f"{TODO_CATEGORIES[0]}"
    JASOSU = f"{TODO_CATEGORIES[1]}"
    GJ_TALK = f"{TODO_CATEGORIES[2]}"
    GENERAL_TALK = f"{TODO_CATEGORIES[3]}"

class RequestItem(BaseModel):
    task: TaskCategory = Field(description="발언에서 추출한 AI가 해야할일. 단 카테고리 중 하나")
    message: str = Field(description="(AI가 해야할일)을 판단한 사용자의 발언 일부")

class GetRequests(BaseModel):
    requests: List[RequestItem] = Field(description="사용자의 요청사항을 분석하여 추출한 작업 목록")

# 정보 추출 
class GetInfo(BaseModel):
    # 사용자 정보
    education: List[enums.E_education] = Field(default_factory=list, description="사용자의 학력") 
    major : List[str] = Field(default_factory=list, description="사용자의 전공들 특별한게 없으면 반드시 빈 리스트를 반환하세요")        # 열거형 없음
    career : List[enums.E_career] = Field(default_factory=list, description="사용자의 경력") 
    licenses : List[enums.E_License] = Field(default_factory=list, description="사용자의 자격증들")
    prefer_condition : List[enums.E_ref_Cond] = Field(default_factory=list, description="우대받을 수 있는 사용자의 조건들 중 사용자에게 해당하는 조건")
    main_experience : List[str] = Field(default_factory=list, description="구직과 자소서 작성에 필요한 주요 경험들을 20자 이내로 짧게 정리. 특별한게 없으면 반드시 빈 리스트를 반환하세요") # 열거형 없음

# 희망 사항 추출 
class GetPrefer(BaseModel):
    pre_salary : List[int] = Field(default_factory=list, description="사용자가 희망하는 최저 연봉(단위:만원) ")  # 열거형 없음
    pre_location : List[enums.E_location] = Field(default_factory=list, description="사용자의 희망 근무지역(시/도) ") 
    pre_industry : List[enums.E_industry] = Field(default_factory=list, description="사용자의 근무희망 산업") 
    pre_role : List[enums.E_role] = Field(default_factory=list, description="사용자의 희망 직무 ") 
    pre_company_type : List[enums.E_company_type] = Field(default_factory=list, description="사용자의 근무희망 기업타입")
    pre_employee_type : List[enums.E_employee_type] = Field(default_factory=list, description="사용자의 희망 근로 형태")
    pre_request : List[str] = Field(default_factory=list, description="희망 기업에 대한 추가적인 조건. 특별한게 없으면 반드시 빈 리스트를 반환하세요")   # 열거형 없음
    