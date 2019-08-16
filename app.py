
from datetime import timedelta

import secrets

from flask import Flask, render_template, session, redirect, url_for, request

import sqlalchemy

import hashlib

SAMPLE_IDEAS = [(0, 'User1', 'Ideia1',
                 '''
1word word word word word word word word word word word word word word word word word word word word word
    2word word word word word word word word word word word word word word word word word word word word word
3word word word word word word word word word word word word word word word word word word word word word
                 '''),
                (1, 'User2', 'Ideia2',
                 ('word word word word word word word word word word word word word word word '
                  'word word word word word word word word word word word word word word word '
                  'word word word word word word word word word word word word word word word '
                  'word word word word word word word word word word word word word word word '
                  'word word word word word word word word word word word word word word word '
                  'word word word word word word word word word word word word word word word '
                  'word word word word word word word word word word word word word word word '
                  'word word word word word word word word word word word word word word word\n'
                  'word word word word word word word word word word word word word word word ')),
                (2, 'User3', 'Ideia3', ''),
                (3, 'User4', 'Ideia4', '')]

app = Flask(__name__)
sql_engine = sqlalchemy.create_engine('sqlite:///app.sqlite')
sql_metadata = sqlalchemy.MetaData()

users_table = sqlalchemy.Table('users', sql_metadata,
                               sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
                               sqlalchemy.Column('name', sqlalchemy.VARCHAR(length=64), unique=True),
                               sqlalchemy.Column('password_hash', sqlalchemy.VARCHAR(length=256)))

def setup_database():

    if not sql_engine.dialect.has_table(sql_engine, 'users'):
        sql_metadata.create_all(sql_engine)

@app.route('/login', methods=['GET', 'POST'])
def login_page():

    if request.method == 'POST':

        session.permanent = True
        username = request.form['user']
        password = request.form['pass']

        sql_connection = sql_engine.connect()

        query = users_table.select().where(sqlalchemy.text(f'name = \'{username}\''))

        result = sql_connection.execute(query)

        user_info = result.first()

        if user_info is None:
            return render_template('login.html', error=True)

        password_hash = user_info[result.keys().index('password_hash')]

        if hashlib.md5(password.encode()).hexdigest() != password_hash:
            return render_template('login.html', error=True)

        session['user'] = username

        return redirect(session.get('login_return_url') or url_for('home_page'))

    return render_template('login.html', error=False)

@app.route('/session_action/logout', methods=['POST'])
def do_logout():

    session['user'] = None
    return 'logout'

@app.route('/ideas', methods=['GET'])
def ideas_page():
    user = session.get('user')
    if user is None:
        session['login_return_url'] = url_for('ideas_page')
        return redirect(url_for('login_page'))

    return render_template('ideas.html', ideas=SAMPLE_IDEAS)

@app.route('/ideas/new', methods=['GET', 'POST'])
def create_idea_page():

    if request.method == 'POST':

        SAMPLE_IDEAS.append((SAMPLE_IDEAS[-1][0] + 1, session.get('user'),
                             request.form['idea-title'], request.form['idea-content']))

        return redirect(url_for('ideas_page'))

    user = session.get('user')
    if user is None:
        session['login_return_url'] = url_for('create_idea_page')
        return redirect(url_for('login_page'))

    return render_template('create_idea.html')

@app.route('/ideas/<int:idea_id>')
def single_idea_page(idea_id):

    for idea in SAMPLE_IDEAS:

        if idea[0] == idea_id:
            return render_template('singleidea.html', idea=idea)

    return 'Invalid', 401

@app.route('/')
def home_page():
    return render_template('home.html')

if __name__ == '__main__':

    setup_database()

    app.permanent_session_lifetime =  timedelta(minutes=20)
    app.secret_key = secrets.token_bytes(8)
    app.config['SESSION_TYPE'] = 'memory'

    app.run(debug=True)
