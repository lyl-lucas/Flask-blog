from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User
from flask.ext.login import current_user


class LoginForm(Form):
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                             Email()])
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')


class RegistrationForm(Form):
    email = StringField('Email', validators=[Required(),
                                             Length(1, 64), Email()])
    username = StringField('Username', validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9]*$', 0,
                                          'Username must only have numbers,'
                                          'letters,dots or underlines')])
    password = PasswordField('Password', validators=[
        Required(), EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('Confirm Password', validators=[Required()])

    submit = SubmitField('Register')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')


class ModifyPasswordForm(Form):
    oldpassword = PasswordField('Previous Password', validators=[Required()])
    newpassword = PasswordField('New Password', validators=[
        Required(), EqualTo('newpassword2', message='Passwords must match.')])
    newpassword2 = PasswordField('Confirm Password', validators=[Required()])
    submit = SubmitField('Submit')

    def validate_oldpassword(self, field):
        if not current_user.verify_password(field.data):
            raise ValidationError('Incorrect Passwords')


class ResetPasswordForm1(Form):
    email = StringField('Email', validators=[Required(),
                                             Length(1, 64), Email()])
    submit = SubmitField('Send Confirmation Email')

    def validate_email(self, field):
        if not User.query.filter_by(email=field.data).first():
            raise ValidationError("Unknown email address")


class ResetPasswordForm2(Form):
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                             Email()])
    newpassword = PasswordField('New Password', validators=[
        Required(), EqualTo('newpassword2', message='Passwords must match.')])
    newpassword2 = PasswordField('Confirm Password', validators=[Required()])
    submit = SubmitField('Submit')

    def validate_email(self, field):
        if not User.query.filter_by(email=field.data).first():
            raise ValidationError("Unknown email address")


class ChangeEmailForm(Form):
    email = StringField('New Email', validators=[Required(), Length(1, 64),
                                                 Email()])
    password = PasswordField('Password', validators=[Required()])
    submit = SubmitField('Update Email Address')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')
