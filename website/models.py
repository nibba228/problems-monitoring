from . import db
from flask_login import UserMixin
from json import dumps


class User(db.Model, UserMixin):
    """Представление пользователя"""
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    name = db.Column(db.String(50))
    password = db.Column(db.String(150))
    
    problems = db.Column(db.String(100000))
    added_problems = db.Column(db.String(30000))
    seen_problems = db.Column(db.String(100000))
    
    update_time = db.Column(db.DateTime(timezone=True), default=None)