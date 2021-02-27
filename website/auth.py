from flask import Blueprint, render_template, request, flash, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from json import dumps, loads
import jmespath as jmp

from .models import User
from . import db
from .problems import get_structure, update_problems


auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Вход"""
    if request.method == 'POST':
        form = request.form
        email = form['email']
        password = form['password']
        
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user, remember=True)
                flash('Вход выполнен успешно!', category='success')
                return redirect(url_for('views.home'))
            else:
                flash('Неверный пароль!', category='error')
        else:
            flash('Такого email не существует!', category='error')
            
    return render_template('login.html', user=current_user)


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    """"Регистрация новых пользователей"""
    
    if request.method == 'POST':
        form = request.form
        
        email = form['email']
        name = form['name']
        password1 = form['password1']
        password2 = form['password2']
        
        # ищем в бд пользователя с таким же email
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Такой email уже существует!', category='error')
        elif len(email) < 4:
            flash('Email должен содержать более 4 символов', category='error')
        elif len(password1) < 8:
            flash('Пароль должен содержать не менее 8 символов', category='error')
        elif password1 != password2:
            flash('Пароли не совпадают!', category='error')
        else:
            problems = get_structure()
            added_problems = update_problems(problems, problems)
            seen_problems = dict.fromkeys(jmp.search('[*].topic.name', added_problems), list())
            
            new_user = User(email=email,
                            name=name,
                            password=generate_password_hash(password1, method='sha256'),
                            problems=dumps(problems),
                            added_problems=dumps(added_problems),
                            seen_problems=dumps(seen_problems))
            
            db.session.add(new_user)
            db.session.commit()
            
            flash('Аккаунт успешно создан!', category='success')
            login_user(new_user, remember=True)
            return redirect(url_for('views.home'))
        
    return render_template('sign_up.html', user=current_user)


@auth.route('/logout')
@login_required
def logout():
    """Выход"""
    logout_user()
    return redirect(url_for('auth.login'))