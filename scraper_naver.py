import asyncio
import os
import csv  # CSV 저장을 위해 추가
import requests
from playwright.async_api import async_playwright
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

async def get_market_data(page, code):
    url = f"https://finance.naver.com/sise/sise_index.naver?code={code}"
    await page.goto(url, wait_until="networkidle")
    
    change_raw = await page.locator("#change_value_and_rate").text_content()
    change_pct = change_raw.split()[-1].replace('(', '').replace(')', '')
    
    amt_raw = await page.locator("th:has-text('거래대금(백만)') + td").text_content()
    amt_trillion = round(int(amt_raw.strip().replace(',', '')) / 1000000, 1)
    
    ant = await page.locator("dl.lst_kos_info dd:nth-of-type(1) span").text_content()
    alien = await page.locator("dl.lst_kos_info dd:nth-of-type(2) span").text_content()
    org = await page.locator("dl.lst_kos_info dd:nth-of-type(3) span").text_content()
    
    return {
        "market": "코스피" if code == "KOSPI" else "코스닥",
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
            
            now = datetime.now()
            date_str = now.strftime('%m월 %d일')
            timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
            
            # 1. 메시지 구성
            message = (
                f"{date_str} KRX 거래대금\n"
                f"코스피 거래대금 {kospi['amt']}조원 {kospi['pct']}\n"
                f"개인 {kospi['ant']}억원 외국인 {kospi['alien']}억원 기관 {kospi['org']}억원\n\n"
                f"코스닥 거래대금 {kosdaq['amt']}조원 {kosdaq['pct']}\n"
                f"개인 {kosdaq['ant']}억원 외국인 {kosdaq['alien']}억원 기관 {kosdaq['org']}억원"
            )

            # --- [추가] 파일 저장 로직 ---
            
            # (A) 텍스트 파일(메모장)로 저장
            with open("market_report.txt", "w", encoding="utf-8") as f:
                f.write(message)
            print("TXT 파일 저장 완료 (market_report.txt)")

            # (B) CSV 파일로 누적 저장 (엑셀용)
            file_exists = os.path.isfile('market_history.csv')
            with open('market_history.csv', 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                # 파일이 처음 생성될 때만 헤더 추가
                if not file_exists:
                    writer.writerow(['일시', '시장', '거래대금(조)', '등락률', '개인', '외국인', '기관'])
                
                writer.writerow([timestamp, kospi['market'], kospi['amt'], kospi['pct'], kospi['ant'], kospi['alien'], kospi['org']])
                writer.writerow([timestamp, kosdaq['market'], kosdaq['amt'], kosdaq['pct'], kosdaq['ant'], kosdaq['alien'], kosdaq['org']])
            print("CSV 파일 저장 완료 (market_history.csv)")

            # 텔레그램 발송 시도 및 응답 확인
            if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
                tg_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                response = requests.post(tg_url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message})
                # 결과 출력 (성공 여부 확인용)
                print(f"텔레그램 응답: {response.json()}") 
            else:
                print("텔레그램 설정이 없어 발송을 건너뜁니다.")

        except Exception as e:
            print(f"에러 발생: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
# import asyncio
# import os
# import requests
# from playwright.async_api import async_playwright
# from datetime import datetime

# TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
# TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# async def get_market_data(page, code):
#     """코스피/코스닥 데이터를 수집하는 공통 함수"""
#     url = f"https://finance.naver.com/sise/sise_index.naver?code={code}"
#     await page.goto(url, wait_until="networkidle")
    
#     # 1. 등락률 (%) - "(+1.87%)" 형태에서 숫자와 기호만 추출
#     change_raw = await page.locator("#change_value_and_rate").text_content()
#     change_pct = change_raw.split()[-1].replace('(', '').replace(')', '')
    
#     # 2. 거래대금 (백만 단위 -> 조 단위 변환)
#     amt_raw = await page.locator("th:has-text('거래대금(백만)') + td").text_content()
#     amt_trillion = round(int(amt_raw.strip().replace(',', '')) / 1000000, 1)
    
#     # 3. 투자자별 매매동향 (개인, 외국인, 기관 - 억 단위)
#     # 플러스(+) 기호는 제거하여 요청하신 양식에 맞춤
#     ant = await page.locator("dl.lst_kos_info dd:nth-of-type(1) span").text_content()
#     alien = await page.locator("dl.lst_kos_info dd:nth-of-type(2) span").text_content()
#     org = await page.locator("dl.lst_kos_info dd:nth-of-type(3) span").text_content()
    
#     return {
#         "amt": amt_trillion,
#         "pct": change_pct,
#         "ant": ant.strip().replace('+', ''),
#         "alien": alien.strip().replace('+', ''),
#         "org": org.strip().replace('+', '')
#     }

# async def run():
#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=True)
#         context = await browser.new_context(
#             user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
#         )
#         page = await context.new_page()
        
#         try:
#             print("데이터 수집 중...")
#             kospi = await get_market_data(page, "KOSPI")
#             kosdaq = await get_market_data(page, "KOSDAQ")
            
#             date_str = datetime.now().strftime('%m월 %d일')
            
#             # 요청하신 양식으로 메시지 구성
#             message = (
#                 f"{date_str} KRX 거래대금\n"
#                 f"코스피 거래대금 {kospi['amt']}조원 {kospi['pct']}\n"
#                 f"개인 {kospi['ant']}억원 외국인 {kospi['alien']}억원 기관 {kospi['org']}억원\n\n"
#                 f"코스닥 거래대금 {kosdaq['amt']}조원 {kosdaq['pct']}\n"
#                 f"개인 {kosdaq['ant']}억원 외국인 {kosdaq['alien']}억원 기관 {kosdaq['org']}억원"
#             )
            
#             # 텔레그램 발송
#             tg_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
#             requests.post(tg_url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message})
#             print(f"발송 완료:\n{message}")

#         except Exception as e:
#             print(f"에러 발생: {e}")
#         finally:
#             await browser.close()

# if __name__ == "__main__":
#     asyncio.run(run())
