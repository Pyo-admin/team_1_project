from flask import Flask, render_template, request
import requests
import xmltodict

app = Flask(__name__)

API_KEY = 'cd2b043a18f246c8b69559e6d0774ba4'
BASE_URL = 'http://www.kopis.or.kr/openApi/restful/pblprfr'

@app.route('/')
def index():
    selected_date = request.args.get('date', '')
    performances = []
    
    if selected_date:
        # 날짜 형식 변환 (YYYY-MM-DD -> YYYYMMDD)
        formatted_date = selected_date.replace('-', '')
        
        # API 호출
        params = {
            'service': API_KEY,
            'stdate': formatted_date,
            'eddate': formatted_date,
            'cpage': '1',
            'rows': '50'
        }
        
        response = requests.get(BASE_URL, params=params)
        
        # XML을 딕셔너리로 변환
        result = xmltodict.parse(response.content)
        
        if 'db' in result['dbs']:
            db_list = result['dbs']['db']
            if not isinstance(db_list, list):
                db_list = [db_list]
            
            for db in db_list:
                perf = {
                    'id': db['mt20id'],
                    'title': db['prfnm'],
                    'place': db['fcltynm'],
                    'poster': db['poster']
                }
                performances.append(perf)
    
    return render_template('index.html', performances=performances, selected_date=selected_date)

@app.route('/detail/<perf_id>')
def detail(perf_id):
    date = request.args.get('date', '')
    
    # 상세 정보 API 호출
    detail_url = f'http://kopis.or.kr/openApi/restful/pblprfr/{perf_id}'
    params = {'service': API_KEY}
    
    response = requests.get(detail_url, params=params)
    
    # XML을 딕셔너리로 변환
    result = xmltodict.parse(response.content)
    db = result['dbs']['db']
    
    detail_info = {
        'title': db['prfnm'],
        'start_date': db['prfpdfrom'],
        'end_date': db['prfpdto'],
        'place': db['fcltynm'],
        'poster': db['poster'],
        'cast': db.get('prfcast', '정보 없음'),
        'runtime': db.get('prfruntime', '정보 없음'),
        'age': db.get('prfage', '정보 없음'),
        'address': db.get('adres', '정보 없음'),
    }
    
    return render_template('detail.html', detail=detail_info, date=date)

if __name__ == '__main__':
    app.run(debug=True)