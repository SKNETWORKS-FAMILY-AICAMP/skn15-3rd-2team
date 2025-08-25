# models.py — 데이터 모델 (pydantic v2 기준)
from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field

class Career(BaseModel):
    level: Optional[str] = None  # 예: 신입, 1-3년, 무관

class PostingDoc(BaseModel):
    gi_no: str
    title: str
    url: str
    jd_text: str = ""
    embed_text: str = ""
    score: Optional[float] = None

class AskTurn(BaseModel):
    field: Optional[str] = None
    ask: str = ""
    options: List[str] = Field(default_factory=list)

class Spec(BaseModel):
    # 필수 축
    location: Optional[str] = None
    career: Career = Field(default_factory=Career)
    employment_type: Optional[str] = None  # 예: 정규직/인턴/계약직/무관
    education: Optional[str] = None        # 예: 고졸/초대졸/대졸(4년)/석사/박사/무관

    # 검색/랭킹 강화 축
    industry: Optional[str] = None
    role: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    major: Optional[str] = None
    certifications: List[str] = Field(default_factory=list)

    # ✅ 추가: 회사 유형(대기업/중견/중소/외국계/공공/스타트업 등)
    company_types: List[str] = Field(default_factory=list)

    # 기타
    job_levels: List[str] = Field(default_factory=list)     # 사원/대리/과장 등
    salary_brackets: List[str] = Field(default_factory=list)
    pref_majors: List[str] = Field(default_factory=list)
    pref_conditions: List[str] = Field(default_factory=list)
    benefits: List[str] = Field(default_factory=list)

def merge_spec(base: Spec, upd: Spec) -> Spec:
    """기존 spec에 새 스펙을 병합(빈 값은 덮어쓰지 않음). 리스트는 합집합."""
    out = base.model_copy(deep=True)

    def _set(attr, val):
        if val is not None and val != "":
            setattr(out, attr, val)

    _set("location", upd.location)
    if upd.career and upd.career.level:
        out.career.level = upd.career.level
    _set("employment_type", upd.employment_type)
    _set("education", upd.education)
    _set("industry", upd.industry)
    _set("role", upd.role)
    _set("major", upd.major)

    for f in ["skills","keywords","certifications","company_types",
              "job_levels","salary_brackets","pref_majors","pref_conditions","benefits"]:
        cur = getattr(out, f) or []
        add = getattr(upd, f) or []
        merged = list(dict.fromkeys([*cur, *add]))
        setattr(out, f, merged)
    return out
