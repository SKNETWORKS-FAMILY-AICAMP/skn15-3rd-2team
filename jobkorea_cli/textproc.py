import re
from typing import List

# 문장/구분자 기반 분리: 종결부호 + 콜론/불릿 뒤 분리
SENT_SPLIT = re.compile(r'(?:(?<=[.!?。…\n])\s+)|(?<=[:\-•·])\s+')

SECT_HEADERS = {
    "duty":    r"(담당\s*업무|업무\s*내용|하는\s*일|what you will do)",
    "must":    r"(자격\s*요건|필수|requirements)",
    "pref":    r"(우대|우대\s*사항|preferred)",
    "stack":   r"(기술|스택|tech|기술\s*스택)",
    "benefit": r"(복리\s*후생|혜택|benefits)"
}
# 섹션 헤더를 한 번에 찾기 위한 통합 정규식
HEADER_RE = re.compile("|".join([f"(?P<{k}>{v})" for k, v in SECT_HEADERS.items()]), re.IGNORECASE)

def split_sentences(text: str) -> List[str]:
    sents = [s.strip() for s in SENT_SPLIT.split(text or "") if s and s.strip()]
    chunks = []
    for s in sents:
        if len(s) <= 400:
            chunks.append(s)
        else:
            # 너무 긴 문장은 400자 단위로 등분
            for i in range(0, len(s), 400):
                chunks.append(s[i:i+400])
    return chunks[:40]

def pick_sections(text: str, per_sect_limit=900, fallback_total=2400) -> str:
    """
    이전 버전은 '헤더 위치부터 per_sect_limit 만큼 잘라옴' → 섹션 중간 절단 빈번.
    → 헤더 간 '구간'을 잘라와 이어 붙임. (다음 헤더 전까지)
    """
    t = re.sub(r"\s+", " ", text or " ").strip()
    matches = [(m.start(), m.lastgroup) for m in HEADER_RE.finditer(t)]
    if not matches:
        return t[:fallback_total]

    # 종단 더미를 추가해 마지막 섹션 범위 계산
    matches.append((len(t), None))
    picks = []
    for i in range(len(matches) - 1):
        start, _ = matches[i]
        end, _   = matches[i+1]
        seg = t[start:min(end, start + per_sect_limit)]
        picks.append(seg)

    joined = " ".join(picks)
    return joined[:fallback_total]

def keyword_windows(text: str, terms: List[str], win=420, max_windows=3) -> str:
    """
    키워드 주변 윈도우를 최대 3개까지 비중복으로 수집 (정확도 ↑)
    """
    if not terms: 
        return ""
    t = re.sub(r"\s+", " ", text or " ").strip()
    low = t.lower()
    hits, seen = [], set()
    for term in terms:
        term = (term or "").strip().lower()
        if not term:
            continue
        for m in re.finditer(re.escape(term), low):
            b = max(0, m.start() - win); e = min(len(t), m.end() + win)
            key = (b // 200, e // 200)
            if key in seen:
                continue
            hits.append(t[b:e]); seen.add(key)
            if len(hits) >= max_windows:
                break
    return " ".join(hits)
