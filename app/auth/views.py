# coding:utf-8
from . import auth
from flask import render_template, redirect,\
    request, url_for, flash
from .forms import LoginForm, RegistrationForm,\
    ModifyPasswordForm, ResetPasswordForm1, ResetPasswordForm2, ChangeEmailForm
from ..models import User
from flask.ext.login import login_user, logout_user,\
    login_required, current_user
from .. import db
from ..email import send_email


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password.')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('YOU have been log out.')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        # 因为需要用到id所以应该先把注册的user提交到数据库中
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email,
                   'Confirm Your Account',
                   'auth/mail/confirm',
                   token=token, user=user)
        flash('A confirmation email has been sent to you by email.')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('You have confirmed your account.Thank you!')
    else:
        flash('This confirm link is invalid or has expired.')
    return redirect(url_for('main.index'))


# 过滤掉未认证的用户
@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed\
                and request.endpoint[:5] != 'auth.'\
                and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html', user=current_user)


@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email,
               'Confirm Your Account',
               'auth/mail/confirm',
               token=token, user=current_user)
    flash('A confirmation email has been sent to you by email.')
    return redirect(url_for('main.index'))


@auth.route('/modifypassword', methods=['GET', 'POST'])
@login_required
def modifypassword():
    form = ModifyPasswordForm()
    if form.validate_on_submit():
        current_user.password = form.newpassword.data
        flash('Passwords have been modified.')
        return redirect(url_for('main.index'))
    return render_template('auth/modifypassword.html', form=form)


@auth.route('/resetpassword', methods=['GET', 'POST'])
def send_resetmail():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm1()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        token = user.generate_confirmation_token()
        send_email(user.email,
                   'Reset Your Passwords',
                   'auth/mail/resetpassword',
                   token=token, user=user)
        flash('A confirmation email has been sent to you by email.' + url_for('auth.resetpassword', token=token, _external=True))
        return redirect(url_for('main.index'))
    return render_template('auth/resetpassword1.html', form=form)


@auth.route('/resetpassword/<token>', methods=['GET', 'POST'])
def resetpassword(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm2()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user.reset_password(token, form.newpassword.data):
            flash('Your password has been reset.')
            return redirect(url_for('auth.login'))
        else:
            flash('This confirm link for reset is invalid or has expired.')
            return redirect(url_for('main.index'))
    return render_template('auth/resetpassword2.html', form=form)


@auth.route('/changeemail', methods=['GET', 'POST'])
@login_required
def send_changeemail():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        token = current_user.generate_change_email_token(form.email.data)
        send_email(form.email.data,
                   'Change Email Link',
                   'auth/mail/changeemailconfirm',
                   token=token)
        flash('A confirmation email has been sent to you by email.')
    return render_template('auth/changeemail.html', form=form)


@auth.route('/changeemail/<token>')
@login_required
def changeemail(token):
    if current_user.confirm_change_email_token(token):
        flash('Email has been updated.')
    else:
        flash('Invalid request.')
    return redirect(url_for('main.index'))
