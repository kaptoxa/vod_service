from data import db
from marshmallow import ValidationError

from config import API_URL, SECRET_KEY
from flask import Flask, request, jsonify, redirect

from data.__all_models import SchemaShortUrl, SchemaLongUrl, LongUrl, ShortUrl


app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY


long_schema = SchemaLongUrl()
short_schema = SchemaShortUrl(only=('url',))


@app.route('/long_to_short/', methods=['POST'])
def long_to_short():
    json_data = request.get_json()
    try:
        data = long_schema.load(json_data)
    except ValidationError as err:
        return jsonify(err.messages), 422

    session = db.create_session()
    long = session.query(LongUrl).filter_by(url=data['url']).first()
    if long is None:
        long = LongUrl(url=data['url'])
        session.add(long)
        session.commit()

        session.add(short_schema.load({'short_link': long.id}))
        session.commit()

    return short_schema.dumps(long.short[-1])


@app.route('/<link>', methods=['GET'])
def transition(link):
    session = db.create_session()
    short = session.query(ShortUrl).filter(ShortUrl.url == link).first()
    if short:
        short.jumps_count += 1
        session.commit()
        return redirect(short.long.url)
    else:
        return jsonify({'error': f'Sorry. We don not have created \'{link}\' short link.'}), 409


@app.route('/statistics/<link>', methods=['GET'])
def statistics(link):
    session = db.create_session()
    short = session.query(ShortUrl).filter(ShortUrl.url == link).first()
    if short:
        return short_schema.dumps(short)
    else:
        return jsonify({'error': f'Sorry. We don not have created \'{link}\' short link.'}), 409


def main():
    db.global_init()
    app.run()


if __name__ == '__main__':
    main()


### TESTS ###

from requests import get, post
link = 'null'

def test_create():
    global link
    params = {"long_url": "http://dirty.ru"}
    response = post(f'{API_URL}/long_to_short/', json=params)
    link = response.json()['short_link']
    assert response.status_code == 200 and link != 'null'


def test_transition():
    global link
    response = get(f'{API_URL}/{link}')
    assert response.status_code == 200


def test_stats():
    global link
    response = get(f'{API_URL}/statistics/{link}')
    assert response.status_code == 200

