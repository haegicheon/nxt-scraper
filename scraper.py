import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # 사람처럼 보이게 설정
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            print("페이지 접속 중...")
            await page.goto("https://www.nextrade.co.kr/menu/marketData/menuList.do", wait_until="networkidle")
            
            # [수정 포인트] 'visible' 상태가 아니더라도 HTML에 존재(attached)하면 통과
            print("데이터 탐색 중...")
            await page.wait_for_selector("#kospiAccTrval", state="attached", timeout=30000)
            
            # 숨겨진 텍스트도 가져올 수 있는 text_content() 사용
            kospi_val = await page.locator("#kospiAccTrval").text_content()
            kosdaq_val = await page.locator("#kosdaqAccTrval").text_content()
            
            # 공백 및 쉼표 제거
            kospi_clean = kospi_val.strip().replace(',', '')
            kosdaq_clean = kosdaq_val.strip().replace(',', '')
            
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            data_line = f"{now}, {kospi_clean}, {kosdaq_clean}\n"
            
            # 파일 저장
            file_path = "nxt_market_data.csv"
            header = "Date, KOSPI_Value, KOSDAQ_Value\n"
            file_exists = os.path.isfile(file_path)
            
            with open(file_path, "a", encoding="utf-8") as f:
                if not file_exists:
                    f.write(header)
                f.write(data_line)
            
            print(f"성공적으로 데이터를 수집했습니다: {data_line}")

        except Exception as e:
            print(f"에러 발생: {e}")
            raise e
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
