import requests
from bs4 import BeautifulSoup

def get_kospi_data():
    url = "https://finance.naver.com/sise/sise_index.naver?code=KOSPI"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        # 네이버 금융은 EUC-KR 인코딩을 사용하는 경우가 많으므로 설정해줍니다.
        response.encoding = 'euc-kr' 
        soup = BeautifulSoup(response.text, 'html.parser')

        # 1. 지수 명칭 (코스피) - image_307029.png 기반
        title = soup.select_one(".sub_tit").get_text(strip=True)

        # 2. 등락률 (1.91%) - image_306d20.jpg 기반
        # span#change_value_and_rate 내부의 텍스트 중 등락률만 추출
        rate_raw = soup.select_one("#change_value_and_rate").get_text(strip=True)
        # 보통 "+114.22+1.91%" 형태로 잡히므로 마지막 % 포함 단어 선택
        rate = rate_raw.split()[-1] 

        # 3. 거래대금 (35.2조) - image_306ca5.png 기반
        # td#amount의 값은 '백만' 단위입니다. (35,284,563 -> 약 35.2조)
        amount_raw = soup.select_one("#amount").get_text(strip=True).replace(",", "")
        amount_trillion = round(int(amount_raw) / 1000000, 1) # 백만 단위를 조 단위로 변환

        # 4. 투자자별 매매동향 - image_30697c.png 기반
        # dd.dd 클래스들을 순서대로 가져옵니다 (개인, 외국인, 기관)
        investors = soup.select(".lst_kos_info dd")
        
        personal = investors[0].select_one("span").get_text(strip=True)
        foreign = investors[1].select_one("span").get_text(strip=True)
        inst = investors[2].select_one("span").get_text(strip=True)

        # 최종 출력 형식 맞추기
        print(f"{title} {rate} {amount_trillion}조")
        print(f"개인 {personal}억 외국인 {foreign}억 기관 {inst}억")

    except Exception as e:
        print(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    get_kospi_data()
