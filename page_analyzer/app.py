import os
import validators
import psycopg2
import requests

from dotenv import load_dotenv
from urllib.parse import urlparse
from flask import (
    Flask, render_template, request,
    flash, redirect, url_for,
    abort)
from bs4 import BeautifulSoup
from page_analyzer.data import UrlRepository

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)
url_repo = UrlRepository(conn)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/urls', methods=['POST'])
def url_post():
    url = request.form['url']
    url_parsed = urlparse(url.lower())
    url_norm = f'{url_parsed.scheme}://{url_parsed.netloc}'

    if len(url_norm) > 255 or not validators.url(url_norm):
        flash('Некорректный URL', 'error')
        return render_template('index.html', form_url=url)

    url_data = url_repo.find_by_name(url_norm)
    if url_data is not None:
        flash('Страница уже существует', 'info')
    else:
        url_data = url_repo.save(url_norm)
        flash('Страница успешно добавлена', 'success')

    return redirect(url_for('url_show', id_=url_data['id']))


@app.route('/urls/<id_>')
def url_show(id_):
    url_data = url_repo.find(id_)
    if url_data is None:
        return abort(404)

    check_data = url_repo.get_all_checks(id_)
    return render_template('urls/show.html',
                           data=url_data,
                           check_data=check_data)


@app.route('/urls')
def urls_index():
    urls_list = url_repo.get_list()
    return render_template('urls/index.html', urls_list=urls_list)


@app.route('/urls/<id_>/checks', methods=['POST'])
def url_check(id_):
    url_data = url_repo.find(id_)

    check_info = check_site(url_data['name'])
    if check_info is None:
        flash('Произошла ошибка при проверке', 'error')
    else:
        check_info['url_id'] = id_
        url_repo.save_check(check_info)
        flash('Страница успешно проверена', 'success')

    return redirect(url_for('url_show', id_=id_))


def check_site(url):
    try:
        r = requests.get(url)
        r.raise_for_status()
    except requests.exceptions.RequestException:
        return None

    check_info = {}
    check_info['status_code'] = r.status_code

    html = r.text
    soup = BeautifulSoup(html, "html.parser")

    if (h1 := soup.find('h1')) is not None:
        check_info['h1'] = h1.text
    if (title := soup.find('title')) is not None:
        check_info['title'] = title.text
    desc = soup.find('meta', attrs={'name': 'description', 'content': True})
    if desc is not None:
        check_info['description'] = desc['content']

    return check_info


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
