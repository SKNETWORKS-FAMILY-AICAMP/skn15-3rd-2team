# ui_schema.py — 문항 UI 스키마/매핑 정의

from __future__ import annotations

# 옵션 후보
DEF_OPTS = {
    "location": ["서울","경기","인천","부산","대구","광주","대전","세종","울산","무관","모름"],
    "education": ["고졸","초대졸","대졸(4년)","석사","박사","무관","모름"],
    "employment_type": ["정규직","계약직","인턴","무관","모름"],
    "career.level": ["신입","경력","무관","모름"],
    "skills": ["Python","SQL","PyTorch","TensorFlow","Docker","AWS","모름"],

    "industry": ["IT/인터넷","제조/생산","금융/은행","공공/기관","교육","모름"],
    "company_types": ["대기업","중견기업","중소기업","외국계","공공기관","스타트업"],
    "job_levels": ["사원","대리","과장","차장","부장","무관"],
    "salary_brackets": ["3000만 이하","3000만-4000만","4000만-5000만","5000만 이상","모름"],
    "pref_conditions": ["재택근무","유연근무","스톡옵션","수평문화","교육지원","모름"],
    "benefits": ["식대제공","법인카드","통신비지원","복지포인트","단체상해보험","모름"],
    "keywords": ["추천","이상탐지","보안","NLP","CV","LLM","모름"],
    "major": ["컴퓨터공학","산업공학","통계학","수학","전자공학","모름"],
    "certifications": ["정보처리기사","SQLD","ADsP","빅분기","TOEIC","OPIC","모름"],
}

# 사용자 노출 라벨
FIELD_LABEL = {
    "location":"근무지역",
    "education":"학력",
    "employment_type":"고용형태",
    "career.level":"경력",
    "skills":"기술 스택",
    "industry":"산업",
    "company_types":"기업형태",
    "job_levels":"직급",
    "salary_brackets":"연봉 구간",
    "pref_conditions":"선호 조건",
    "benefits":"복리후생",
    "keywords":"키워드",
    "major":"전공",
    "certifications":"자격증",
}

# 질문 템플릿
DEF_ASK = {
    "location": "근무 희망 지역을 선택/입력해 주세요. (예: 서울)",
    "education": "최종 학력을 선택해 주세요. (예: 대졸(4년))",
    "employment_type": "희망 고용형태를 선택해 주세요. (예: 정규직/계약직/인턴/무관)",
    "career.level": "경력 수준을 선택해 주세요. (예: 신입/경력/무관)",
    "skills": "사용 가능한 기술 스택을 입력해 주세요. (예: Python, SQL, PyTorch)",
    "industry": "관심 산업을 선택/입력해 주세요. (예: IT/인터넷)",
    "company_types": "선호 기업형태를 선택해 주세요. (예: 대기업/스타트업)",
    "job_levels": "희망 직급을 선택해 주세요. (예: 사원/대리/과장)",
    "salary_brackets": "희망 연봉 구간을 선택해 주세요. (예: 4000만-5000만)",
    "pref_conditions": "선호하는 근무 조건을 선택해 주세요. (예: 재택근무/유연근무)",
    "benefits": "중요하게 생각하는 복리후생을 선택해 주세요. (예: 식대제공/복지포인트)",
    "keywords": "검색에 반영할 키워드를 입력해 주세요. (예: 추천, 이상탐지, NLP)",
    "major": "전공을 입력해 주세요. (예: 컴퓨터공학)",
    "certifications": "보유 자격증을 입력/선택해 주세요. (예: 정보처리기사, SQLD)",
}
