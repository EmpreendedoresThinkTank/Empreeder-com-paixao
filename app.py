
from datetime import timedelta

import secrets

from flask import Flask, render_template, session, redirect, url_for, request

app = Flask(__name__)

@app.route('/login', methods=['GET', 'POST'])
def login_page():

    if request.method == 'POST':

        session.permanent = True
        session['user'] = request.form['user']

        return redirect(session.get('login_return_url') or url_for('home_page'))

    return render_template('login.html')

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

    ideas = [('User1', 'Ideia1', None),
             ('User2', 'Ideia2', None),
             ('User3', 'Ideia3', None),
             ('User4', 'Ideia4', None)]

    return render_template('ideas.html', ideas=ideas)

@app.route('/')
def home_page():
    return render_template('home.html')

if __name__ == '__main__':

    app.permanent_session_lifetime =  timedelta(minutes=20)
    app.secret_key = secrets.token_bytes(8)
    app.config['SESSION_TYPE'] = 'memory'

    app.run(debug=True)
