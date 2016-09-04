from flask import Flask
from flask import make_response
from flask.ext.script import Manager
from flask import render_template
from flask.ext.bootstrap import Bootstrap
app = Flask(__name__)
manager = Manager(app)
bootstrap = Bootstrap(app)


@app.route('/')
def index():
    resp = make_response(render_template('index.html'))
    resp.set_cookie('answer', '42')
    return resp


@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == "__main__":
    manager.run()
