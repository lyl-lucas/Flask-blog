from flask import Flask
from flask import make_response
from flask.ext.script import Manager
app = Flask(__name__)
manager = Manager(app)


@app.route('/')
def index():
    resp = make_response('<h1>Hello World !</h1>')
    resp.set_cookie('answer', '42')
    return resp


@app.route('/user/<name>')
def user(name):
    return '<h1>Hello %s' % name

if __name__ == "__main__":
    manager.run()
