from enum import Enum

USER_INFO = [
    "education",
    "major",
    "career",
    "licenses",
    "prefer_condition",
    "main_experience",
    "pre_salary",
    "pre_location",
    "pre_industry",
    "pre_role",
    "pre_company_type",
    "pre_employee_type",
    "pre_request",
]




TODO_CATEGORIES = [
    "구직활동 돕기",
    "자소서 돕기",
    "구직 및 자소서 관련 대화",
    "기타 대화 혹은 알 수 없음",
    ]

def convert_enum_to_string(obj):
    if isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, list):
        return [convert_enum_to_string(item) for item in obj]
    else:
        return obj