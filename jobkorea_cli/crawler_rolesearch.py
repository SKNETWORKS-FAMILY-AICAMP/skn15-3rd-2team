# crawler_rolesearch.py — expanded_roles 각 키워드로 2건씩 빠른 서치 수집(제목 보강판)
from __future__ import annotations
import re
from urllib.parse import quote_plus
from typing import List, Dict, Tuple

from playwright.async_api import async_playwright, TimeoutError as PWTimeout
from .models import PostingDoc

BASE = "https://www.jobkorea.co.kr"

def _normalize_gi(url: str) -> str:
    """항상 BASE + /Recruit/GI_Read/{id} 형태로 정규화."""
    if not url:
        return ""
    u = url.strip()
    m = re.search(r"/Recruit/GI_Read/(\d+)", u)
    if m:
        return f"{BASE}/Recruit/GI_Read/{m.group(1)}"
    if u.startswith("http"):
        return u
    return BASE + (u if u.startswith("/") else "/" + u)

async def _collect_topk_urls_from_search(page, role_kw: str, per_role: int) -> List[str]:
    """
    현재 page에서 role_kw로 검색 후, GI_Read 링크 상위 per_role개 url만 추출
    """
    q = quote_plus(role_kw)
    search_url = f"{BASE}/Search/?stext={q}&tabType=recruit"
    await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)

    hrefs = await page.eval_on_selector_all(
        "a[href*='/Recruit/GI_Read/']",
        "els => els.map(e => e.getAttribute('href'))"
    )

    out: List[str] = []
    seen = set()
    for href in hrefs or []:
        if not href:
            continue
        norm = _normalize_gi(href)
        m = re.search(r"/Recruit/GI_Read/(\d+)", norm)
        if not m:
            continue
        gid = m.group(1)
        if gid in seen:
            continue
        seen.add(gid)
        out.append(norm)
        if len(out) >= per_role:
            break
    return out

def _extract_title_from_html(html: str) -> str:
    # og:title 우선
    m = re.search(r'<meta\s+property=["\']og:title["\']\s+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    # h1 보조
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()
    # <title>
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()
    return ""

async def _fetch_title_with_fallback(page, url: str) -> str:
    """
    상세 페이지로 짧게 진입해 제목 확보:
      1) page.title()
      2) og:title / h1 / title 파싱
    """
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
    except PWTimeout:
        return ""
    except Exception:
        return ""

    # 1) 브라우저 title API
    try:
        t = await page.title()
        if t and t.strip():
            return t.strip()
    except Exception:
        pass

    # 2) HTML 파싱
    try:
        html = await page.content()
        t = _extract_title_from_html(html)
        if t:
            return t
    except Exception:
        pass

    # 3) 화면 내 주요 제목 후보 셀렉터 시도(페이지 구조가 바뀌는 경우 대비)
    for sel in [
        "h1", ".tit", ".title", ".detailArea h1", ".devViewContents h1",
        ".recruitMent h1", ".tbRow h1", "#detailArea h1"
    ]:
        try:
            loc = page.locator(sel).first
            if await loc.count():
                txt = (await loc.inner_text()).strip()
                if txt:
                    return txt
        except Exception:
            continue

    return ""

async def crawl_by_roles_multi(expanded_roles: List[str], per_role: int = 2) -> Dict[str, List[PostingDoc]]:
    """
    expanded_roles의 각 키워드로 검색하여 per_role개씩 수집.
    각 상세 페이지에 짧게 진입해서 제목을 확실히 확보.
    반환: { role_kw: [PostingDoc, ...], ... }
    """
    result: Dict[str, List[PostingDoc]] = {}
    if not expanded_roles:
        return result

    # 중복 제거 + 순서 유지
    roles: List[str] = []
    seen = set()
    for r in expanded_roles:
        k = (r or "").strip()
        if not k or k in seen:
            continue
        seen.add(k)
        roles.append(k)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()

        for role_kw in roles:
            urls = await _collect_topk_urls_from_search(page, role_kw, per_role)
            docs: List[PostingDoc] = []
            for url in urls:
                gid_match = re.search(r"/Recruit/GI_Read/(\d+)", url)
                gid = gid_match.group(1) if gid_match else url

                # 같은 탭(page)로 빠르게 타이틀만 긁고 돌아옴
                title = await _fetch_title_with_fallback(page, url)
                if not title:
                    title = "(제목 없음)"

                docs.append(PostingDoc(
                    gi_no=gid,
                    title=title,
                    url=url,
                    jd_text="",     # 속도 우선: 필요하면 이후 단계에서 상세 텍스트 수집
                    embed_text=""
                ))
            result[role_kw] = docs

        await browser.close()

    return result
