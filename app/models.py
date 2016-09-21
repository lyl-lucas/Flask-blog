# coding:utf-8
from . import db
from werkzeug.security import generate_password_hash, \
    check_password_hash
from flask.ext.login import UserMixin, AnonymousUserMixin
from . import login_manager
from flask import current_app, request
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from datetime import datetime
import hashlib
from markdown import markdown
import bleach


class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py
        from sqlalchemy.exc import IntegrityError

        seed()
        user_count = User.query.count()
        for i in range(count):
            follower = User.query.offset(randint(0, user_count - 1)).first()
            followed = User.query.offset(randint(0, user_count - 1)).first()
            f = Follow(follower=follower,
                       followed=followed,
                       timestamp=forgery_py.date.date(True))
            db.session.add(f)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()


class Permission:
        FOLLOW = 0x01  # 关注用户
        COMMENT = 0x02  # 评论
        WRITE_ARTICLES = 0x04  # 写文章
        MODERATE_COMMENTS = 0x08  # 管理修改和谐评论
        ADMINISTER = 0x80  # 管理网站


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permission = db.Column(db.Integer)
    # 一对多
    users = db.relationship('User', backref='role', lazy='dynamic')

    # 方便Role对象输入到数据库中
    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.FOLLOW |
                     Permission.COMMENT |
                     Permission.WRITE_ARTICLES, True),
            'Moderator': (Permission.FOLLOW |
                          Permission.COMMENT |
                          Permission.WRITE_ARTICLES |
                          Permission.MODERATE_COMMENTS, False),
            'Administrator': (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.default = roles[r][1]
            role.permission = roles[r][0]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)

    name = db.Column(db.String(64))  # 真实姓名
    location = db.Column(db.String(64))  # 所在地
    about_me = db.Column(db.Text())  # 个人简介
    # 注册日期,创建时会自动赋值
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)  # 最后访问日期

    avatar_hash = db.Column(db.String(32))
    # 一对多
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    # 自引用多对多关系
    followers = db.relationship('Follow', foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')
    followed = db.relationship('Follow', foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASK_ADMIN']:
                self.role = Role.query.filter_by(permission=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()

        if self.email and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(
                self.email.encode('utf-8')).hexdigest()

    # 通过property来对password进行一些预处理以保存哈希值
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        # 因为需要用到id所以应该先把注册的user提交到数据库中
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        # 解码时不需要提供expiration
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        # 在认证用户版本中,confirmed写错成confirm
        self.confirmed = True
        db.session.add(self)
        return True

    def reset_password(self, token, newpassword):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.password = newpassword
        db.session.add(self)
        return True

    def generate_change_email_token(self, newemail, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'email': self.email, 'new email': newemail})

    def confirm_change_email_token(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if self.email != data.get('email'):
            return False
        if data.get('new email') is None:
            return False
        newemail = data.get('new email')
        if User.query.filter_by(email=newemail).first():
            return False
        self.email = newemail
        self.avatar_hash = hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

    def can(self, permission):
        return self.role.permission and\
            (self.role.permission & permission) == permission

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError  # integrity有保存的意思
        from random import seed
        import forgery_py

        seed()  # 保证每次调用生成的用户名序列不同,默认参数是系统时间
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(),
                     username=forgery_py.internet.user_name(True),
                     password=forgery_py.lorem_ipsum.word(),
                     confirmed=True,
                     name=forgery_py.name.full_name(),
                     location=forgery_py.address.city(),
                     about_me=forgery_py.lorem_ipsum.sentence(),
                     member_since=forgery_py.date.date(True))
            db.session.add(u)
            # 防止出现email重复而提交不了的情况
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    # 关注关系常用函数
    def follow(self, user):
        if not self.is_following(user):
            # 关注方式就是在关联表中加入表示关系的行
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self, user):
        return self.followed.filter_by(
            followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        return self.followers.filter_by(
            follower_id=user.id).first() is not None

    def __repr__(self):
        return '<User %r>' % self.username


# 博客文章的模型
class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    # 和users表存在一对多关系
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul', 'h1',
                        'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(markdown(
            value, output_format='html'),
            tags=allowed_tags, strip=True))

    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()
        for i in range(count):
            user = User.query.offset(randint(0, user_count - 1)).first()
            post = Post(body=forgery_py.lorem_ipsum.sentences(randint(1, 3)),
                        timestamp=forgery_py.date.date(True),
                        author=user)
            db.session.add(post)
            db.session.commit()


db.event.listen(Post.body, 'set', Post.on_changed_body)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class AnonymousUser(AnonymousUserMixin):
    def can(self, permission):
        return False

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)


login_manager.anonymous_user = AnonymousUser
