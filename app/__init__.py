# coding:utf-8
from flask import Flask, render_template
from flask.ext.bootstrap import Bootstrap
from flask.ext.moment import Moment
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.mail import Mail
from config import config

bootstrap = Bootstrap()
moment = Moment()
db = SQLAlchemy()
mail = Mail()


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    mail.init_app(app)

    # 路由和错误信息定义的视图函数
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint, url_prefix='/main')

    return app
