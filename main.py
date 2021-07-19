from data import db
from marshmallow import ValidationError

from config import API_URL, SECRET_KEY
from flask import Flask, request, jsonify, redirect, render_template

from data.__all_models import SchemaShortUrl, SchemaLongUrl, LongUrl, ShortUrl

from requests import get, post


app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = SECRET_KEY


long_schema = SchemaLongUrl()
short_schema = SchemaShortUrl(only=('url',))


@app.route('/create/', methods=['POST'])
def long_to_short():
    json_data = request.get_json()
    try:
        data = long_schema.load(json_data)
    except ValidationError as err:
        return jsonify(err.messages), 422

    session = db.create_session()
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
        if short.jumps_count > 1:
            session.delete(short.long)
            session.delete(short)
            session.commit()
            return jsonify({'error': f'Sorry. This link is not more existing...'}), 409
        session.commit()
        return render_template('index.html', videoname=f"{short.long.url}.mp4")
    else:
        return jsonify({'error': f'Sorry. We do not have created this link.'}), 409


def main():
    db.global_init()
    app.run()


if __name__ == '__main__':
    main()


### TESTS ###

link = 'null'

def test_create():
    global link
    params = {"long_url": "Опять двойка"}
    response = post(f'{API_URL}/create/', json=params)
    link = response.json()['short_link']
    assert response.status_code == 200 and link != 'null'


def test_transition():
    global link
    response = get(f'{API_URL}/{link}')
    assert response.status_code == 200


def test_twice():
    global link
    response = get(f'{API_URL}/{link}')
    assert response.status_code == 409

