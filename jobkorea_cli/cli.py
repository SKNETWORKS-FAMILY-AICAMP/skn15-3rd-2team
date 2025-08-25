# cli.py — expanded_roles 각 키워드당 2건씩 역할별 검색 후 출력
from __future__ import annotations
import asyncio, sys

from .models import Spec
from .llm import parse_spec, ask_required_batch, map_filters
from .crawler_rolesearch import crawl_by_roles_multi

def _missing_required(s: Spec) -> list[str]:
    m = []
    if not (s.career and s.career.level): m.append("career.level")
    if not s.location: m.append("location")
    if not s.employment_type: m.append("employment_type")
    if not s.education: m.append("education")
    return m

async def _interactive_spec() -> Spec:
    print("예) 서울 거주 신입, 4년제 졸, 파이썬/SQL 가능, 정보처리기사 보유, 통계학 전공")
    user_text = input("입력> ").strip()
    spec = await parse_spec(user_text)

    miss = _missing_required(spec)
    if miss:
        print("[필수 정보 확인중 ...]")
        turns = await ask_required_batch(spec, miss)
        for t in turns:
            # 질문 문구/옵션 안전 처리
            ask = getattr(t, "ask", "") or "값을 입력해 주세요."
            options = getattr(t, "options", []) or []
            field = getattr(t, "field", None)

            print(ask)
            if options:
                print("선택지:", ", ".join(options))
            ans = input("답변> ").strip()
            if not ans:
                continue

            if field == "career.level":
                spec.career.level = ans
            elif field == "location":
                spec.location = ans
            elif field == "employment_type":
                spec.employment_type = ans
            elif field == "education":
                spec.education = ans
            elif field == "skills":
                spec.skills = [s.strip() for s in ans.split(",") if s.strip()]
            elif field == "certifications":
                spec.certifications = [s.strip() for s in ans.split(",") if s.strip()]
            elif field == "major":
                spec.major = ans
    return spec

async def main():
    print("=== 잡코리아 역할별 빠른 서치 (expanded_roles 기반) ===")
    print("종료: exit/quit\n")

    spec = await _interactive_spec()

    # LLM 매핑(여기서 expanded_roles 생성)
    applied = await map_filters(spec)

    print("\n[적용된 키워드]")
    print("- expanded_roles:", applied.get("expanded_roles") or [])
    print("- keywords:", applied.get("keywords") or [])

    expanded_roles = applied.get("expanded_roles") or []
    if not expanded_roles:
        print("\n[결과] expanded_roles가 비어 있습니다. 입력 문장을 더 구체적으로 써 주세요.")
        return

    # 직무 키워드별 2건씩 수집
    grouped = await crawl_by_roles_multi(expanded_roles, per_role=2)

    # 출력
    any_hit = False
    print("\n[역할별 Top 2]")
    for role_kw in expanded_roles:
        docs = grouped.get(role_kw, [])
        print(f"\n▶ {role_kw}")
        if not docs:
            print("  - (결과 없음)")
            continue
        any_hit = True
        for d in docs:
            print(f"  - {d.title if d.title else '(제목 없음)'}")
            print(f"    링크: {d.url}")
    if not any_hit:
        print("\n(모든 역할에서 결과 없음)")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n종료합니다.")
        sys.exit(0)
