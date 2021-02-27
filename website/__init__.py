from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os.path

from .config import Config


db = SQLAlchemy()


def create_app():
    # инициализация приложения и базы данных
    app = Flask(__name__)
    config = Config()
    app.config.from_object(config)
    db.init_app(app)
    
    # это выражение позволяет нам использовать zip в jinja 2 как фильтр
    app.jinja_env.filters['zip'] = zip
    
    # регистрация блюпринтов
    from .views import views
    from .auth import auth
    
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    
    # создание таблиц бд
    from .models import User
    create_database(app)
    
    # инициализация системы пользователей
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    return app


def create_database(app):
    if not os.path.exists('website/' + app.config['DB_NAME']):
        db.create_all(app=app)