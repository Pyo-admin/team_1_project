from flask import Flask, render_template, request
import requests
import xmltodict

app = Flask(__name__)

SERVICE_KEY = "a07ca300-683b-45fd-bb84-c9dbdd4a976e"
API_URL = "https://api.kcisa.kr/openapi/service/rest/meta4/getKCPG0504"

@app.route("/", methods=["GET", "POST"])
def index():
    results = []
    keyword = ""
    
    if request.method == "POST":
        keyword = request.form.get("keyword", "").strip()
        
        params = {
            "serviceKey": SERVICE_KEY,
            "numOfRows": "50",
            "pageNo": "1"
        }

        response = requests.get(API_URL, params=params)
        if response.status_code == 200:
            data_dict = xmltodict.parse(response.text)
            try:
                items = data_dict['response']['body']['items']['item']
                if isinstance(items, dict):
                    items = [items]
                
                # 통합 검색: title, eventPeriod, spatialCoverage
                if keyword:
                    items = [
                        item for item in items
                        if keyword in str(item.get("title", "")) 
                        or keyword in str(item.get("eventPeriod", ""))
                        or keyword in str(item.get("spatialCoverage", ""))
                    ]
                
                results = items
            except KeyError:
                results = []

    return render_template("exam.html", results=results, keyword=keyword)

if __name__ == "__main__":
    app.run(debug=True)
