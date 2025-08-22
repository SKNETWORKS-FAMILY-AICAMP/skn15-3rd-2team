def search_jobs(keyword: str, location: str = "서울") -> str:
    # 예시 검색 결과 반환
    if "데이터 분석가" in keyword:
        return """
[1] 데이터 분석가 - 카카오엔터프라이즈 (https://www.jobkorea.co.kr/Recruit/GI_Read/12345678)
[2] 주니어 데이터 분석가 - 네이버 (https://www.jobkorea.co.kr/Recruit/GI_Read/23456789)
[3] 데이터 사이언티스트 인턴 - 쿠팡 (https://www.jobkorea.co.kr/Recruit/GI_Read/34567890)
"""
    return "해당 키워드의 공고를 찾을 수 없습니다."