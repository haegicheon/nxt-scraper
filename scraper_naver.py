import asyncio
import os
import requests
from playwright.async_api import async_playwright
from datetime import datetime

# 텔레그램 설정 (기존에 등록한 GitHub Secrets 사용)
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

async def run():
    async with async_playwright() as p:
        # 브라우저 실행
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            # 네이버 증권 코스피 페이지 접속
            url = "https://finance.naver.com/sise/sise_index.naver?code=KOSPI"
            await page.goto(url, wait_until="networkidle")
            
            # 1. 지수 및 등락 정보 수집
            index_val = await page.locator("#now_value").text_content()
            change_val = await page.locator("#change_value_and_rate").text_content()
            
            # 2. 거래대금 수집 (백만 단위 -> 조 단위 변환)
            # '거래대금(백만)' 텍스트 옆에 있는 수치를 가져옵니다.
            amount_raw = await page.locator("th:has-text('거래대금(백만)') + td").text_content()
            amount_num = int(amount_raw.strip().replace(',', ''))
            amount_trillion = round(amount_num / 1000000, 1) # 백만 단위이므로 100만으로 나누면 조 단위가 됩니다.
            
            # 3. 투자자별 매매동향 (개인, 외국인, 기관 - 억 단위)
            # 이미지에서 확인한 dl.lst_kos_info 구조를 활용합니다.
            ant = await page.locator("dl.lst_kos_info dd:nth-of-type(1) span").text_content()
            alien = await page.locator("dl.lst_kos_info dd:nth-of-type(2) span").text_content()
            org = await page.locator("dl.lst_kos_info dd:nth-of-type(3) span").text_content()
            
            # 메시지 구성
            date_str = datetime.now().strftime('%m월 %d일')
            # 등락 정보 줄바꿈 및 공백 정리
            clean_change = " ".join(change_val.split())
            
            message = (
                f"{date_str} 코스피 지수\n"
                f"지수: {index_val.strip()} ({clean_change})\n"
                f"거래대금: {amount_trillion}조원\n"
                f"개인: {ant.strip()}억 / 외국인: {alien.strip()}억 / 기관: {org.strip()}억"
            )
            
            # 텔레그램 발송
            tg_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
            requests.post(tg_url, json=payload)
            print(f"성공: {message}")

        except Exception as e:
            print(f"에러 발생: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
