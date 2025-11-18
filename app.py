from flask import Flask, render_template, request, jsonify, Response
import requests
import xmltodict
import os
import base64
from datetime import datetime

app = Flask(__name__)

API_KEY = 'cd2b043a18f246c8b69559e6d0774ba4' # KOPIS 공연 정보 API 정보
BASE_URL = 'http://www.kopis.or.kr/openApi/restful/pblprfr'
SAVE_FOLDER = 'saved_screenshots'  # 화면 캡처 저장 폴더 이름

if not os.path.exists(SAVE_FOLDER): # 저장 폴더가 없으면 자동 생성
    os.makedirs(SAVE_FOLDER)


@app.route('/') # 메인 페이지 (선택한 날짜에 해당하는 공연 목록 조회)
def index():
    selected_date = request.args.get('date', '') # 사용자 날짜 선택
    selected_genres = request.args.getlist('genres') # 사용자 장르 리스트 선택
    performances = [] # 화면에 전달할 공연 리스트

    if selected_date: # 날짜가 선택된 경우에만 API 요청 진행
        formatted_date = selected_date.replace('-', '') # KOPIS API 형식은 YYYYMMDD -> 날짜에서 '-' 제거
        all_performances = [] # 공연 리스트 임시 저장
        seen_ids = set() # 중복 제거를 위한 집합

        genres_to_search = selected_genres or [None]  # 장르가 선택되지 않았으면 전체 검색
        for genre in genres_to_search: # 선택된 장르(또는 전체)를 반복하며 API 요청
            params = { #API 요청에 필요한 파라미터
                'service': API_KEY,
                'stdate': formatted_date, # 조회 시작일
                'eddate': formatted_date, # 조회 종료일
                'cpage': '1', # 페이지 번호
                'rows': '50' # 한 번에 가져올 데이터 개수
            }

            if genre: # 장르가 선택된 경우에만 파라미터 추가
                params['shcate'] = genre

            response = requests.get(BASE_URL, params=params) # KOPIS API 호출
            result = xmltodict.parse(response.content) # XML 데이터를 dict(딕셔너리)로 변환

            if 'dbs' in result and result['dbs'] and 'db' in result['dbs']: # 공연 DB 목록이 존재하는 확인
                db_list = result['dbs']['db']
                if not isinstance(db_list, list): # 단일 객체면 리스트로 변환
                    db_list = [db_list]
                for db in db_list: # 공연 리스트 반복
                    perf_id = db.get('mt20id')
                    if perf_id and perf_id not in seen_ids: # 이미 추가된 공연이면 스킵 (중복 제거)
                        perf = {
                            'id': perf_id,
                            'title': db.get('prfnm', '제목 없음'),
                            'place': db.get('fcltynm', '장소 없음'),
                            'poster': db.get('poster', ''),
                            'genre': db.get('genrenm', '')
                        }
                        all_performances.append(perf)
                        seen_ids.add(perf_id)

        performances = all_performances # 최종 공연 리스트

    return render_template('index.html', #index.html 렌더링
                           performances=performances,
                           selected_date=selected_date,
                           selected_genres=selected_genres)


@app.route('/detail/<perf_id>') # 공연 상세 페이지
def detail(perf_id):
    date = request.args.get('date', '') # 목록에서 보던 날짜 (뒤로가기 시 유지용)
    detail_url = f'{BASE_URL}/{perf_id}' # 상세 정보 API 요청 URL
    params = {'service': API_KEY}

    response = requests.get(detail_url, params=params) # 상세 정보 요청
    result = xmltodict.parse(response.content)

    if 'dbs' in result and 'db' in result['dbs']: # 공연 정보가 존재하는지 확인
        db = result['dbs']['db']
    else:
        return "해당 공연 정보를 찾을 수 없습니다.", 404

    detail_info = { # HTML에 전달할 상세 정보 딕셔너리
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


@app.route('/proxy_image') # 이미지 proxy (URL -> 직접 표시)
def proxy_image():
    image_url = request.args.get('url')
    if not image_url:
        return "No URL provided", 400
    try:
        resp = requests.get(image_url, stream=True) # 실제 이미지 요청
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection'] # 브라우저가 충돌할 수 있는 헤더 제거
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]
        return Response(resp.content, resp.status_code, headers) # 이미지 데이털를 그대로 반환
    except Exception as e:
        return str(e), 500


@app.route('/save_screenshot', methods=['POST']) # 페이지 캡처 저장
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
        safe_title = "".join(c for c in (title or "") if c.isalnum() or c in (' ', '_', '-')).strip() or "performance" # 파일명 안전하게 변환
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S') # 파일명에 날짜시각 추가
        filename = f"{safe_title}_{timestamp}.png"
        filepath = os.path.join(SAVE_FOLDER, filename)

        with open(filepath, 'wb') as f: # 실제 파일 저장
            f.write(image_bytes)

        abs_filepath = os.path.abspath(filepath) # 절대 경로 반환

        return jsonify({
            'success': True,
            'message': f'페이지가 저장되었습니다!\n\n파일명: {filename}\n경로: {abs_filepath}'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'저장 실패: {str(e)}'})

if __name__ == '__main__': # Flask 서버 실행
    app.run(debug=True)
