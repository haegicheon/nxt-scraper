import requests
from bs4 import BeautifulSoup
import re
import os

# 텔레그램 설정 (본인의 정보를 입력하세요)
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')


def send_telegram_message(message):
# 1. 토큰이 제대로 들어왔는지 먼저 확인
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ 오류: 깃허브 Secrets에 토큰이나 ID가 설정되지 않았습니다.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    # 2. 전송 시도 후 결과 받기
    response = requests.post(url, json=payload)
    
    # 3. 결과 출력 (GitHub Actions 로그에서 확인 가능)
    if response.status_code == 200:
        print("✅ 텔레그램 전송 성공!")
    else:
        print(f"❌ 전송 실패! 상태 코드: {response.status_code}")
        print(f"❌ 에러 내용: {response.text}") # 텔레그램이 보내준 에러 메시지 출력

# 스크래핑 대상
codes = ["KOSPI", "KOSDAQ"]
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
}

final_report = "<b>📊 오늘의 증시 요약</b>\n\n"

for code in codes:
    url = f"https://finance.naver.com/sise/sise_index.naver?code={code}"
    response = requests.get(url, headers=headers)
    response.encoding = 'euc-kr' 
    soup = BeautifulSoup(response.text, 'html.parser')

    try:
        market_name = soup.select_one('h3.sub_tlt').get_text(strip=True)
        
        rate_el = soup.select_one('#change_value_and_rate')
        text = rate_el.get_text(strip=True) if rate_el else ""
        match = re.search(r'[+-]?[\d,.]+\%', text)
        rate = match.group() if match else ""
        status = "상승" if "+" in rate else "하락" if "-" in rate else "보합"

        amount_el = soup.select_one('#amount')
        amount_raw = amount_el.get_text(strip=True).replace(',', '') if amount_el else "0"
        amount_trillion = round(int(amount_raw) / 1000000, 1)

        investors = soup.select('dl.lst_kos_info dd.dd')
        inv_dict = {item.get_text(separator="|").split("|")[0].strip(): 
                    item.find('span').get_text(strip=True) for item in investors[:3]}

        # 보고서 문구 생성
        final_report += f"<b>[{market_name}]</b> {rate}{status} {amount_trillion}조\n"
        final_report += f"👤개인 {inv_dict.get('개인')} 👽외인 {inv_dict.get('외국인')} 🏛기관 {inv_dict.get('기관')}\n"
        final_report += "-" * 20 + "\n"

    except Exception as e:
        final_report += f"{code} 에러 발생: {e}\n"

# 텔레그램 전송
send_telegram_message(final_report)
print("텔레그램 전송 완료!")
