import requests
import xmltodict
import json

# API 호출
SERVICE_KEY = "a07ca300-683b-45fd-bb84-c9dbdd4a976e"  # 본인의 서비스키
API_URL = "https://api.kcisa.kr/openapi/service/rest/meta4/getKCPG0504"

params = {
    "serviceKey": SERVICE_KEY,
    "numOfRows": "10",  # 가져올 데이터 수
    "pageNo": "1"       # 페이지 번호
}

response = requests.get(API_URL, params=params)

if response.status_code != 200:
    print("API 호출 실패:", response.status_code)
    exit()

# XML → dict 변환
xml_data = response.text
data_dict = xmltodict.parse(xml_data)

# items가 존재하는지 확인
try:
    items = data_dict['response']['body']['items']['item']
    # 단일 데이터인 경우 list로 변환
    if isinstance(items, dict):
        items = [items]
except KeyError:
    print("데이터가 없습니다.")
    exit()

# JSON 저장
with open("festival_data.json", "w", encoding="utf-8") as f:
    json.dump(items, f, ensure_ascii=False, indent=4)

# XML 저장 
def list_to_xml(data_list):
    xml = "<festivals>\n"
    for item in data_list:
        xml += "  <festival>\n"
        for key, value in item.items():
            xml += f"    <{key}>{value}</{key}>\n"
        xml += "  </festival>\n"
    xml += "</festivals>"
    return xml

xml_data = list_to_xml(items)
with open("festival_data.xml", "w", encoding="utf-8") as f:
    f.write(xml_data)

# TXT 저장
with open("festival_data.txt", "w", encoding="utf-8") as f:
    for item in items:
        f.write(f"축제명: {item.get('title', '')}\n")
        f.write(f"설명: {item.get('description', '')}\n")
        f.write(f"기간: {item.get('eventPeriod', '')}\n")
        f.write(f"장소: {item.get('spatialCoverage', '')}\n")
        f.write(f"링크: {item.get('url', '')}\n")
        f.write("="*50 + "\n")

print("JSON, XML, TXT 파일로 저장 완료!")
