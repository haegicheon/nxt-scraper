import asyncio
import os
import requests
from playwright.async_api import async_playwright
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

async def get_market_data(page, code):
    """코스피/코스닥 데이터를 수집하는 공통 함수"""
    url = f"https://finance.naver.com/sise/sise_index.naver?code={code}"
    await page.goto(url, wait_until="networkidle")
    
    # 1. 등락률 (%) - "(+1.87%)" 형태에서 숫자와 기호만 추출
    change_raw = await page.locator("#change_value_and_rate").text_content()
    change_pct = change_raw.split()[-1].replace('(', '').replace(')', '')
    
    # 2. 거래대금 (백만 단위 -> 조 단위 변환)
    amt_raw = await page.locator("th:has-text('거래대금(백만)') + td").text_content()
    amt_trillion = round(int(amt_raw.strip().replace(',', '')) / 1000000, 1)
    
    # 3. 투자자별 매매동향 (개인, 외국인, 기관 - 억 단위)
    # 플러스(+) 기호는 제거하여 요청하신 양식에 맞춤
    ant = await page.locator("dl.lst_kos_info dd:nth-of-type(1) span").text_content()
    alien = await page.locator("dl.lst_kos_info dd:nth-of-type(2) span").text_content()
    org = await page.locator("dl.lst_kos_info dd:nth-of-type(3) span").text_content()
    
    return {
        "amt": amt_trillion,
        "pct": change_pct,
        "ant": ant.strip().replace('+', ''),
        "alien": alien.strip().replace('+', ''),
        "org": org.strip().replace('+', '')
    }

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            print("데이터 수집 중...")
            kospi = await get_market_data(page, "KOSPI")
            kosdaq = await get_market_data(page, "KOSDAQ")
            
            date_str = datetime.now().strftime('%m월 %d일')
            
            # 요청하신 양식으로 메시지 구성
            message = (
                f"{date_str} KRX 거래대금\n"
                f"코스피 거래대금 {kospi['amt']}조원 {kospi['pct']}\n"
                f"개인 {kospi['ant']}억원 외국인 {kospi['alien']}억원 기관 {kospi['org']}억원\n\n"
                f"코스닥 거래대금 {kosdaq['amt']}조원 {kosdaq['pct']}\n"
                f"개인 {kosdaq['ant']}억원 외국인 {kosdaq['alien']}억원 기관 {kosdaq['org']}억원"
            )
            
            # 텔레그램 발송
            tg_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            requests.post(tg_url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message})
            print(f"발송 완료:\n{message}")

        except Exception as e:
            print(f"에러 발생: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
