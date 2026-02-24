import asyncio
import os
import requests
from playwright.async_api import async_playwright
from datetime import datetime

# 텔레그램 설정 (GitHub Secrets에 등록할 값들)
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0...")
        page = await context.new_page()
        
        try:
            await page.goto("https://www.nextrade.co.kr/menu/marketData/menuList.do", wait_until="networkidle")
            await page.wait_for_selector("#kospiAccTrval", state="attached", timeout=30000)
            
            # 데이터 추출
            kospi_raw = await page.locator("#kospiAccTrval").text_content()
            kosdaq_raw = await page.locator("#kosdaqAccTrval").text_content()
            
            # 숫자로 변환 (쉼표 제거)
            kospi_num = int(kospi_raw.strip().replace(',', ''))
            kosdaq_num = int(kosdaq_raw.strip().replace(',', ''))
            
            # '조' 단위로 변환 및 반올림 (예: 17,575... -> 17.6)
            kospi_trillion = round(kospi_num / 10**12, 1)
            kosdaq_trillion = round(kosdaq_num / 10**12, 1)
            
            # 메시지 구성
            date_str = datetime.now().strftime('%m월 %d일')
            message = (
                f"{date_str} NXT 거래대금\n"
                f"코스피: {kospi_trillion}조원\n"
                f"코스닥: {kosdaq_trillion}조원"
            )
            
            # 텔레그램 발송
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
            requests.post(url, json=payload)
            print(f"메시지 발송 완료: {message}")

        except Exception as e:
            print(f"에러: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())

# import asyncio
# from playwright.async_api import async_playwright
# from datetime import datetime
# import os

# async def run():
#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=True)
#         # 사람처럼 보이게 설정
#         context = await browser.new_context(
#             user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
#         )
#         page = await context.new_page()
        
#         try:
#             print("페이지 접속 중...")
#             await page.goto("https://www.nextrade.co.kr/menu/marketData/menuList.do", wait_until="networkidle")
            
#             # [수정 포인트] 'visible' 상태가 아니더라도 HTML에 존재(attached)하면 통과
#             print("데이터 탐색 중...")
#             await page.wait_for_selector("#kospiAccTrval", state="attached", timeout=30000)
            
#             # 숨겨진 텍스트도 가져올 수 있는 text_content() 사용
#             kospi_val = await page.locator("#kospiAccTrval").text_content()
#             kosdaq_val = await page.locator("#kosdaqAccTrval").text_content()
            
#             # 공백 및 쉼표 제거
#             kospi_clean = kospi_val.strip().replace(',', '')
#             kosdaq_clean = kosdaq_val.strip().replace(',', '')
            
#             now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#             data_line = f"{now}, {kospi_clean}, {kosdaq_clean}\n"
            
#             # 파일 저장
#             file_path = "nxt_market_data.csv"
#             header = "Date, KOSPI_Value, KOSDAQ_Value\n"
#             file_exists = os.path.isfile(file_path)
            
#             with open(file_path, "a", encoding="utf-8") as f:
#                 if not file_exists:
#                     f.write(header)
#                 f.write(data_line)
            
#             print(f"성공적으로 데이터를 수집했습니다: {data_line}")

#         except Exception as e:
#             print(f"에러 발생: {e}")
#             raise e
#         finally:
#             await browser.close()

# if __name__ == "__main__":
#     asyncio.run(run())
