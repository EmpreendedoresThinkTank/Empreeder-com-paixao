
from datetime import timedelta

import secrets

from flask import Flask, render_template, session, redirect, url_for, request

import sqlalchemy

import hashlib

app = Flask(__name__)
sql_engine = sqlalchemy.create_engine('sqlite:///app.sqlite')
sql_metadata = sqlalchemy.MetaData()

users_table = sqlalchemy.Table('users', sql_metadata,
                               sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
                               sqlalchemy.Column('name', sqlalchemy.VARCHAR(length=64), unique=True),
                               sqlalchemy.Column('password_hash', sqlalchemy.VARCHAR(length=256)))

ideas_table = sqlalchemy.Table('ideas', sql_metadata,
                               sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
                               sqlalchemy.Column('user', sqlalchemy.Integer),
                               sqlalchemy.Column('title', sqlalchemy.VARCHAR(length=64)),
                               sqlalchemy.Column('content', sqlalchemy.Text()))

sql_metadata.create_all(sql_engine)

@app.route('/login', methods=['GET', 'POST'])
def login_page():

    if request.method == 'POST':

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

        session.permanent = True
        session['user'] = username
        session['user_id'] = user_info[result.keys().index('id')]

        return redirect(session.get('login_return_url') or url_for('home_page'))

    return render_template('login.html', error=False)

@app.route('/signup', methods=['GET', 'POST'])
def signup_page():

    if request.method == 'POST':

        username = request.form['user']
        password = request.form['pass']

        sql_connection = sql_engine.connect()

        query = users_table.insert().values(name=username,
                                            password_hash=hashlib.md5(password.encode()).hexdigest())

        result = sql_connection.execute(query)

        session.permanent = True
        session['user'] = username
        session['user_id'] = result.inserted_primary_key

        return redirect(url_for('home_page'))

    return render_template('signup.html')

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

    sql_connection = sql_engine.connect()

    query = users_table.select()

    result = sql_connection.execute(query)

    users_id_index = result.keys().index('id')
    users_name_index = result.keys().index('name')
    users = {user_info[users_id_index]: user_info[users_name_index] for user_info in result}

    query = ideas_table.select().order_by(ideas_table.c.id.desc())

    result = sql_connection.execute(query)

    ideas_table_columns = result.keys()

    table_indexes = (ideas_table_columns.index('id'),
                     ideas_table_columns.index('user'),
                     ideas_table_columns.index('title'),
                     ideas_table_columns.index('content'))

    ideas = tuple(tuple((idea[index] if i != 1 else users.get(idea[index])
                         for i, index in enumerate(table_indexes))) for idea in result)

    return render_template('ideas.html', ideas=ideas)

@app.route('/ideas/new', methods=['GET', 'POST'])
def create_idea_page():

    if request.method == 'POST':

        sql_connection = sql_engine.connect()

        query = ideas_table.insert().values(user=session.get('user_id'),
                                            title=request.form['idea-title'],
                                            content=request.form['idea-content'])

        sql_connection.execute(query)

        return redirect(url_for('ideas_page'))

    user = session.get('user')
    if user is None:
        session['login_return_url'] = url_for('create_idea_page')
        return redirect(url_for('login_page'))

    return render_template('create_idea.html')

@app.route('/session_action/ideas/delete/<int:idea_id>', methods=['POST'])
def do_delete_idea(idea_id):

    sql_connection = sql_engine.connect()

    query = ideas_table.select().where(sqlalchemy.text(f'id = {idea_id}'))

    result = sql_connection.execute(query)

    idea_info = result.first()
    if idea_info is None:
        return 'Invalid', 401

    if idea_info[result.keys().index('user')] != session['user_id']:
        return 'Invalid', 401

    query = ideas_table.delete().where(sqlalchemy.text(f'id = {idea_id}'))

    sql_connection.execute(query)

    return 'deleted'

@app.route('/ideas/<int:idea_id>')
def single_idea_page(idea_id):

    sql_connection = sql_engine.connect()

    query = ideas_table.select().where(sqlalchemy.text(f'id = {idea_id}'))

    result = sql_connection.execute(query)

    idea_info = result.first()
    if idea_info is None:
        return 'Invalid', 401

    ideas_table_columns = result.keys()
    table_indexes = (ideas_table_columns.index('id'),
                     ideas_table_columns.index('user'),
                     ideas_table_columns.index('title'),
                     ideas_table_columns.index('content'))

    query = users_table.select().where(sqlalchemy.text(f'id = {idea_info[table_indexes[1]]}'))

    result = sql_connection.execute(query)

    user_info = result.first()

    if user_info is None:
        return 'Invalid', 401

    author = user_info[result.keys().index('name')]

    idea = tuple((idea_info[index] if i != 1 else author for i, index in enumerate(table_indexes)))

    return render_template('singleidea.html', idea=idea)

@app.route('/')
def home_page():

    all_buttons_info = (('lamp_symbol.png', ('POSTAR UMA IDEIA',), url_for('create_idea_page')),
                        ('money_symbol.png', ('INVESTIR EM UMA IDEIA',), url_for('ideas_page')),
                        ('heart_symbol.png', ('POSTAR UMA DOR',), '.'),
                        ('puzzle_symbol.png', ('SOLUCIONAR UMA DOR',), '.'),
                        ('two_people_symbol.png', ('MENTORIA OU MENTORAR',), '.'),
                        ('files_symbol.png', ('ARTIGOS E DOCUMENTOS',), '.'),
                        ('blog_symbol.png', ('BLOG DOS', 'EMPREENDEDORES'), '.'))

    return render_template('home.html', all_buttons_info=all_buttons_info)

if __name__ == '__main__':

    app.permanent_session_lifetime =  timedelta(minutes=20)
    app.secret_key = secrets.token_bytes(8)
    app.config['SESSION_TYPE'] = 'memory'

    app.run(debug=True)
