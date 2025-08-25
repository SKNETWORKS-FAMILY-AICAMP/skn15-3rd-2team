# role_map.py — 기술/키워드 → 직무 매핑

# 기술/스택 → 대표 직무
SKILL_TO_ROLE = {
    # 백엔드/플랫폼
    "python": "백엔드 개발자",
    "django": "백엔드 개발자",
    "fastapi": "백엔드 개발자",
    "spring": "백엔드 개발자",
    "node": "백엔드 개발자",
    "go": "백엔드 개발자",
    "kotlin": "백엔드 개발자",
    "kafka": "백엔드 개발자",
    "redis": "백엔드 개발자",
    "mysql": "백엔드 개발자",
    "postgres": "백엔드 개발자",

    # 프론트엔드/웹
    "react": "프론트엔드 개발자",
    "vue": "프론트엔드 개발자",
    "typescript": "프론트엔드 개발자",
    "next.js": "프론트엔드 개발자",

    # 모바일
    "android": "모바일 앱 개발자",
    "ios": "모바일 앱 개발자",
    "swift": "모바일 앱 개발자",
    "flutter": "모바일 앱 개발자",
    "react native": "모바일 앱 개발자",

    # 데이터/AI
    "sql": "데이터 분석가",
    "pandas": "데이터 분석가",
    "spark": "데이터 엔지니어",
    "airflow": "데이터 엔지니어",
    "etl": "데이터 엔지니어",
    "ml": "머신러닝 엔지니어",
    "machine learning": "머신러닝 엔지니어",
    "deep learning": "딥러닝 엔지니어",
    "pytorch": "딥러닝 엔지니어",
    "tensorflow": "딥러닝 엔지니어",
    "nlp": "nlp 엔지니어",
    "llm": "ai 엔지니어",
    "cv": "컴퓨터비전 엔지니어",
    "computer vision": "컴퓨터비전 엔지니어",
    "mle": "머신러닝 엔지니어",
    "ds": "데이터 사이언티스트",
    "data scientist": "데이터 사이언티스트",

    # DevOps/클라우드
    "aws": "데브옵스 엔지니어",
    "gcp": "데브옵스 엔지니어",
    "azure": "데브옵스 엔지니어",
    "docker": "데브옵스 엔지니어",
    "kubernetes": "데브옵스 엔지니어",
    "k8s": "데브옵스 엔지니어",
    "terraform": "데브옵스 엔지니어",

    # 보안/테스트
    "security": "보안 엔지니어",
    "pentest": "보안 엔지니어",
    "qa": "qa 엔지니어",
    "cicd": "데브옵스 엔지니어",
}

# 직무 동의어/라벨 변형 → 대표 직무
ROLE_ALIASES = {
    "백엔드": "백엔드 개발자",
    "backend": "백엔드 개발자",
    "서버개발": "백엔드 개발자",
    "플랫폼": "백엔드 개발자",
    "프론트": "프론트엔드 개발자",
    "frontend": "프론트엔드 개발자",
    "웹퍼블리셔": "프론트엔드 개발자",
    "앱": "모바일 앱 개발자",
    "ios개발": "모바일 앱 개발자",
    "android개발": "모바일 앱 개발자",
    "데이터엔지니어": "데이터 엔지니어",
    "데이터분석": "데이터 분석가",
    "데이터사이언티스트": "데이터 사이언티스트",
    "머신러닝": "머신러닝 엔지니어",
    "딥러닝": "딥러닝 엔지니어",
    "ai": "ai 엔지니어",
    "mlops": "데브옵스 엔지니어",
    "devops": "데브옵스 엔지니어",
    "보안": "보안 엔지니어",
    "qa테스터": "qa 엔지니어",
}

def canonical_role(raw: str | None) -> str | None:
    if not raw: return None
    r = raw.strip().lower()
    return ROLE_ALIASES.get(r, raw)

def role_from_skills(skills: list[str] | None) -> str | None:
    if not skills: return None
    for s in skills:
        k = (s or "").strip().lower()
        if not k: continue
        if k in SKILL_TO_ROLE:
            return SKILL_TO_ROLE[k]
    return None
