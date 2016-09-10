from flask import render_template, session, \
    redirect, url_for, flash, current_app, abort
from . import main
from .forms import NameForm
from ..models import User
from .. import db
from ..email import send_email
from datetime import datetime


@main.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user = User(username=form.name.data)
            db.session.add(user)
            session['known'] = False
            if current_app.config['FLASK_ADMIN']:
                send_email(current_app.config['FLASK_ADMIN'],
                           'new user', 'mail/new_user',
                           user=user)
        else:
            session['known'] = True
        old_name = session.get('name')
        if old_name is not None and old_name != form.name.data:
            flash('You are not the one who came last moment.')
        session['name'] = form.name.data
        return redirect(url_for('.index'))
    return render_template('index.html', form=form,
                           name=session.get('name'),
                           known=session.get('known')
                           )


@main.route('/user/<name>')
def user(name):
    abort(404)
    return render_template('user.html', name=name,
                           current_time=datetime.utcnow())
