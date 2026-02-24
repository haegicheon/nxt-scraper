import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        # 사이트 접속
        await page.goto("https://www.nextrade.co.kr/menu/marketData/menuList.do")
        # 데이터가 나타날 때까지 최대 10초 대기
        await page.wait_for_selector("#kospiAccTrval", timeout=10000)
        
        # 데이터 추출
        kospi_val = await page.inner_text("#kospiAccTrval")
        kosdaq_val = await page.inner_text("#kosdaqAccTrval")
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # 쉼표 제거 및 데이터 정리
        data_line = f"{now}, {kospi_val.replace(',', '')}, {kosdaq_val.replace(',', '')}\n"
        
        # 파일 저장
        file_path = "nxt_market_data.csv"
        if not os.path.exists(file_path):
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("Date, KOSPI_Value, KOSDAQ_Value\n")
        
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(data_line)
            
        print(f"Success: {data_line}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
