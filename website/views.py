from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from json import loads, dumps
import jmespath as jmp
from datetime import datetime

from . import db
from .problems import get_structure, update_problems, merge_added_problems
from .parser import url


views = Blueprint('views', __name__)


@views.route('/')
@login_required
def home():
    new_problems = get_structure()
    new_added_problems = update_problems(loads(current_user.problems), new_problems)
    added_problems = merge_added_problems(current_user, new_added_problems, new_problems)
    
    update_time_str = datetime.strftime(current_user.update_time, '%d %b в %H:%M:%S, %Y год')
    
    # делаем выборку тем и списков заданий
    topics = jmp.search('[*].topic', added_problems)
    all_problems = jmp.search('[*].problems', added_problems)
    
    any_problems = any(all_problems)
    return render_template('home.html',
                           user=current_user,
                           topics=topics,
                           all_problems=all_problems,
                           any_problems=any_problems,
                           url=url,
                           update_time=update_time_str,
                           seen_problems=loads(current_user.seen_problems))


@views.route('/seen-problems')
@login_required
def seen_problems():
    """Просмотренные пользователем задания"""
    seen_problems = loads(current_user.seen_problems)
    any_seen = any(seen_problems.values())
    return render_template('seen_problems.html',
                           user=current_user,
                           any_seen=any_seen,
                           seen_problems=seen_problems,
                           url=url)
    

@views.route('/make-seen', methods=['POST'])
def make_seen():
    data = loads(request.data)
    user_id = int(data['userId'])
    problem_id = data['problemId']
    topic_name = data['topicName']

    if user_id == current_user.id:
        seen_problems = loads(current_user.seen_problems)
        seen_problems[topic_name].append(problem_id)
        current_user.seen_problems = dumps(seen_problems)
            
        db.session.commit()
    
    return jsonify({})