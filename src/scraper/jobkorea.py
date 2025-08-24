import asyncio
from playwright.async_api import async_playwright, Page, expect, TimeoutError, Error
import re

async def click_available_element(page: Page, selector: str, text: str):
    base_locator = page.locator(f'{selector}:has-text("{text}")')
    try:
        await base_locator.nth(0).click(timeout=1000)
        return 
    except Error as e:
        pass
    try:
        await base_locator.nth(1).click(timeout=1000)
        return 
    except Error as e:
        raise e
    
async def initialize_and_goto(url: str) -> Page:
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=False)
    page = await browser.new_page()
    await page.goto(url, wait_until="domcontentloaded")
    return page

async def click_job_button_on_page(page: Page, info1, info2):
    for con in info1:   # 2단계 검색
        await page.locator(f'p.btn_tit:has-text("{con[0]}"), button.btn_tit:has-text("{con[0]}")').click() # 둘중하나로 카테고리 선택
        await click_available_element(page=page, selector='span.radiWrap', text=con[1] )
        await click_available_element(page=page, selector='span.radiWrap', text=con[2] )

    for con in info2:
        await page.locator(f'p.btn_tit:has-text("{con[0]}"), button.btn_tit:has-text("{con[0]}")').click() # 둘중하나로 카테고리 선택
        await click_available_element(page=page, selector='span.radiWrap', text=con[1] )
            
    # 검색
    search_button = page.get_by_role("button", name="선택된 조건 검색하기")
    await search_button.click()
    
    # 검색 완료 대기
    await page.locator('#dev-btn-search[disabled]:has-text("검색완료")').wait_for(state="visible", timeout=5000)