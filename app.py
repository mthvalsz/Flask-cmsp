from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests
import re

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Chave secreta para a sessão

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        ra = request.form['ra']
        password = request.form['password']
        
        urlLogin = "https://edusp-api.ip.tv/registration/edusp"
        headersLogin = {
            'Content-Type': 'application/json',
            'x-api-realm': 'edusp',
            'x-api-platform': 'webclient',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Origin': 'https://cmspweb.ip.tv',
            'Referer': 'https://cmspweb.ip.tv/',
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'pt-BR,pt;q=0.9',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
        }

        dataLogin = {
            "realm": "edusp",
            "platform": "webclient",
            "id": ra,
            "password": password
        }

        responseLogin = requests.post(urlLogin, headers=headersLogin, json=dataLogin)

        if responseLogin.status_code == 200:
            responseL_json = responseLogin.json()
            if 'auth_token' in responseL_json:
                session['auth_tokenAPI'] = responseL_json['auth_token']
                return redirect(url_for('materias'))
            else:
                flash("Chave 'auth_token' não encontrada no JSON.")
        else:
            flash(f'Request failed with status code: {responseLogin.text}')

    return render_template('index.html')

@app.route('/materias', methods=['GET', 'POST'])
def materias():
    auth_tokenAPI = session.get('auth_tokenAPI')
    if not auth_tokenAPI:
        return redirect(url_for('index'))

    url = "https://edusp-api.ip.tv/room/user?list_all=true&with_cards=true"
    headers = {
        "x-api-key": auth_tokenAPI,
        "referer": "https://cmspweb.ip.tv/"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        response_json = response.json()
        if 'rooms' in response_json:
            session['alunoKEY'] = response_json['rooms'][0]['name']
        else:
            flash("Chave 'rooms' não encontrada no JSON.")
            return redirect(url_for('index'))
    else:
        flash("Falha ao fazer a solicitação GET:", response.status_code)
        return redirect(url_for('index'))

    urlMat = f"https://edusp-api.ip.tv/tms/task/todo/categories?publication_target[]={session['alunoKEY']}&publication_target[]=762"
    headersMat = {
        "x-api-key": auth_tokenAPI
    }

    responseMat = requests.get(urlMat, headers=headersMat)
    if responseMat.status_code == 200:
        dataMat = responseMat.json()
        return render_template('materias.html', materias=dataMat)
    else:
        flash("Falha ao fazer GET das matérias.")
        return redirect(url_for('index'))

@app.route('/atividades/<idMateria>', methods=['GET', 'POST'])
def atividades(idMateria):
    auth_tokenAPI = session.get('auth_tokenAPI')
    alunoKEY = session.get('alunoKEY')
    if not auth_tokenAPI or not alunoKEY:
        return redirect(url_for('index'))

    urlAtv = f"https://edusp-api.ip.tv/tms/task/todo?expired_only=false&publication_target[]={alunoKEY}&publication_target[]=762&limit=100&filter_expired=true&category_id={idMateria}&offset=0"
    headersAtv = {
        "x-api-key": auth_tokenAPI
    }

    responseAtv = requests.get(urlAtv, headers=headersAtv)
    if responseAtv.status_code == 200:
        dataAtv = responseAtv.json()
        return render_template('atividades.html', atividades=dataAtv, idMateria=idMateria)
    else:
        flash("Falha ao fazer GET das atividades.")
        return redirect(url_for('materias'))

@app.route('/respostas/<atividadeId>', methods=['GET'])
def respostas(atividadeId):
    auth_tokenAPI = session.get('auth_tokenAPI')
    if not auth_tokenAPI:
        return redirect(url_for('index'))

    urlQst = f"https://edusp-api.ip.tv/tms/task/{atividadeId}?with_questions=true&with_assessed_skills=true&with_target=true"
    headersQst = {
        "x-api-key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJza2V5IjoiYXV0aF90b2tlbjplZHVzcDpyZW5hdG9lZHVhcmRvODI3MjIwMi1zcCIsIm5pY2siOiJyZW5hdG9lZHVhcmRvODI3MjIwMi1zcCIsInJvbGUiOiIwMDA0IiwicmVhbG0iOiJlZHVzcCIsImlhdCI6MTcxMTE0OTU1MSwiYXVkIjoiZGFzaGJvYXJkIn0.yMAH2YqzKRmqhQxSw-VCKZK-WozwhSheK530lKJruUM"
    }

    response = requests.get(urlQst, headers=headersQst)
    if response.status_code == 200:
        dataQst = response.json()
        questions = dataQst.get('questions', [])
        questions.sort(key=lambda x: x['order'])
        return render_template('respostas.html', questions=questions)
    else:
        flash("Falha ao fazer a solicitação GET:", response.status_code)
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
