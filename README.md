# Flask-blog
学习Flask web 开发,并部署在heroku上，https://lucasflask.herokuapp.com
可使用账号    cat@house.com : ilovefish 登录尝试

##主要功能
- 用户注册,登录,登出
- 注册邮箱认证 
- 用户信息操作:修改个人密码,修改邮箱(需重新认证),修改个人资料
- 权限管理,管理员可以修改用户信息和管理评论
- 文章发表,支持markdown功能,文章编辑
- 评论文章功能
- 用户关注功能,主页可选择显示关注文章或所有文章
- 用户avator头像
- RESTFul api可用账号连接http://lucasflask.herokuapp.com/api/v1.0/posts尝试

##主要涉及扩展模块
- 使用flask-script支持命令行选项
- 使用jinja渲染页面
- 使用Bootstrap，flask-bootstrap,flask-moment等处理网页前端内容
- 使用flask-wtf处理表单,并带有跨站伪造保护
- 使用flask-sqlalchemy和关系型数据库(sqlite和postgresql)
- 使用flask-migrate进行数据库的迁移工作
- 使用flask-mail和itsdangerous生成用户邮箱确认信息
- 使用flask-login管理用户的登录登出状态
- 使用flask-pagedown支持markdown功能
- 使用flask-HTTPAuth实现RESTful api的认证用户功能
- 使用coverage统计单元测试覆盖率
- 使用selenium进行端到端测试
- 使用flask-SSLify启用https
