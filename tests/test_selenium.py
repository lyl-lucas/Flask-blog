# -*- coding: utf-8 -*-
from selenium import webdriver
import unittest
from app import create_app, db
from app.models import Role, User, Post
import threading
import re


class SeleniumTestCase(unittest.TestCase):
    client = None

    @classmethod
    def setUpClass(cls):
        # 启动firefox
        try:
            cls.client = webdriver.Firefox()
        except:
            pass
        # 如果无法启动跳过这些测试
        if cls.client:
            cls.app = create_app('testing')
            cls.app_context = cls.app.app_context()
            cls.app_context.push()

            # 禁止日志,保证输出整洁
            import logging
            logger = logging.getLogger('werkzeug')
            logger.setLevel('ERROR')

            # 创建数据库,并使用一些虚拟数据填充
            db.create_all()
            Role.insert_roles()
            User.generate_fake(10)
            Post.generate_fake(10)

            # 添加管理员
            admin_role = Role.query.filter_by(permission=0xff).first()
            admin = User(email='lucas@example.com',
                         username='Lucas',
                         password='cat',
                         role=admin_role, confirmed=True)
            db.session.add(admin)
            db.session.commit()

            # 在一个线程中启动Flask服务器
            threading.Thread(target=cls.app.run).start()

    @classmethod
    def tearDownClass(cls):
        if cls.client:
            # 关闭服务器
            cls.client.get('http://localhost:5000/shutdown')
            cls.client.close()

            # 销毁数据库
            db.drop_all()
            db.session.remove()

            cls.app_context.pop()

    def setUp(self):
        if not self.client:
            self.skipTest('Web browser not available')

    def tearDown(self):
        pass

    def test_admin_home_page(self):
        # 进入首页
        self.client.get('http://localhost:5000')
        self.assertTrue(re.search('Hello,\s+world',
                                  self.client.page_source))
        self.client.find_element_by_link_text('Sign In').click()
        self.assertTrue('<h1>Login</h1>' in self.client.page_source)

        # 输入账号密码登录
        self.client.find_element_by_name('email').send_keys('lucas@example.com')
        self.client.find_element_by_name('password').send_keys('cat')
        self.client.find_element_by_name('submit').click()
        self.assertTrue(re.search('Hello,\s+Lucas',
                                  self.client.page_source))

        # 测试发表新post
        self.client.find_element_by_name('body').send_keys('test for writing a new post.')
        self.client.find_element_by_name('submit').click()
        self.assertTrue('test for writing a new post.' in self.client.page_source)

        self.client.find_element_by_link_text('Profile').click()
        self.assertTrue('<h1>Lucas</h1>' in self.client.page_source)
