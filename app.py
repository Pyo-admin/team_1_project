from flask import Flask, render_template, request, jsonify, Response
import requests
import xmltodict
import os
import base64
from datetime import datetime

app = Flask(__name__)

API_KEY = 'cd2b043a18f246c8b69559e6d0774ba4'
BASE_URL = 'http://www.kopis.or.kr/openApi/restful/pblprfr'
SAVE_FOLDER = 'saved_screenshots'

if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)

@app.route('/')
def index():
    selected_date = request.args.get('date', '')
    selected_genres = request.args.getlist('genres')
    performances = []

    if selected_date:
        formatted_date = selected_date.replace('-', '')
        all_performances = []
        seen_ids = set()

        # 장르가 선택되지 않았으면 전체 검색
        genres_to_search = selected_genres or [None]
        for genre in genres_to_search:
            params = {
                'service': API_KEY,
                'stdate': formatted_date,
                'eddate': formatted_date,
                'cpage': '1',
                'rows': '50'
            }
            if genre:
                params['shcate'] = genre

            response = requests.get(BASE_URL, params=params)
            result = xmltodict.parse(response.content)

            if 'dbs' in result and result['dbs'] and 'db' in result['dbs']:
                db_list = result['dbs']['db']
                if not isinstance(db_list, list):
                    db_list = [db_list]

                for db in db_list:
                    perf_id = db.get('mt20id')
                    if perf_id and perf_id not in seen_ids:
                        perf = {
                            'id': perf_id,
                            'title': db.get('prfnm', '제목 없음'),
                            'place': db.get('fcltynm', '장소 없음'),
                            'poster': db.get('poster', ''),
                            'genre': db.get('genrenm', '')
                        }
                        all_performances.append(perf)
                        seen_ids.add(perf_id)

        performances = all_performances

    return render_template('index.html',
                           performances=performances,
                           selected_date=selected_date,
                           selected_genres=selected_genres)

@app.route('/detail/<perf_id>')
def detail(perf_id):
    date = request.args.get('date', '')
    detail_url = f'{BASE_URL}/{perf_id}'
    params = {'service': API_KEY}

    response = requests.get(detail_url, params=params)
    result = xmltodict.parse(response.content)

    if 'dbs' in result and 'db' in result['dbs']:
        db = result['dbs']['db']
    else:
        return "해당 공연 정보를 찾을 수 없습니다.", 404

    detail_info = {
        'id': perf_id,
        'title': db.get('prfnm', '제목 없음'),
        'start_date': db.get('prfpdfrom', ''),
        'end_date': db.get('prfpdto', ''),
        'place': db.get('fcltynm', ''),
        'poster': db.get('poster', ''),
        'genre': db.get('genrenm', '정보 없음'),
        'cast': db.get('prfcast', '정보 없음'),
        'runtime': db.get('prfruntime', '정보 없음'),
        'age': db.get('prfage', '정보 없음'),
        'address': db.get('adres', '정보 없음'),
        'price': db.get('pcseguidance', '정보 없음')
    }

    return render_template('detail.html', detail=detail_info, date=date)

@app.route('/proxy_image')
def proxy_image():
    image_url = request.args.get('url')
    if not image_url:
        return "No URL provided", 400
    try:
        resp = requests.get(image_url, stream=True)
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]
        return Response(resp.content, resp.status_code, headers)
    except Exception as e:
        return str(e), 500

@app.route('/save_screenshot', methods=['POST'])
def save_screenshot():
    try:
        data = request.json
        image_data = data.get('image_data')
        title = data.get('title')

        if not image_data:
            return jsonify({'success': False, 'message': '이미지 데이터가 없습니다.'})

        if ',' in image_data:
            image_data = image_data.split(',')[1]

        image_bytes = base64.b64decode(image_data)
        safe_title = "".join(c for c in (title or "") if c.isalnum() or c in (' ', '_', '-')).strip() or "performance"
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{safe_title}_{timestamp}.png"
        filepath = os.path.join(SAVE_FOLDER, filename)

        with open(filepath, 'wb') as f:
            f.write(image_bytes)

        abs_filepath = os.path.abspath(filepath)

        return jsonify({
            'success': True,
            'message': f'페이지가 저장되었습니다!\n\n파일명: {filename}\n경로: {abs_filepath}'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'저장 실패: {str(e)}'})

if __name__ == '__main__':
    app.run(debug=True)
