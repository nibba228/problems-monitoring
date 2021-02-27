from json import loads, dumps
from bs4 import Tag
import re
import jmespath as jmp
import numpy as np
from flask_login import UserMixin

from .parser import get_catalog, get_problems


# при использовании вложенных списков выскакивают предупреждения.
# данное выражение позволяет их игнорировать
np.warnings.filterwarnings('ignore', category=np.VisibleDeprecationWarning)


def get_structure() -> list:
    """Создание структуры данных для заданий"""

    # получаем категории заданий и url страницы с ними
    catalog = get_catalog()
    structure = []
    for topic in catalog:
        section = {'topic': __create_topic_dict(topic),
                   'subtopics': __create_subtopic_list(topic)}
        structure.append(section)

    return structure


def update_problems(old_structure: list, new_structure: list) -> list:
    """
    Создание структуры данных с числами, означающими сколько было
    добавлено новых заданий, и списками со ссылками на новые задания
    """
    # upd от слова update
    upd_structure = []

    # вытягиваем названия тем
    topic_names = jmp.search('[*].topic.name', old_structure)

    # считаем дельту кол-в заданий по подтемам, преобразовывая списки в списке в np.array,
    # чтобы можно было вычитать
    new_sbt_counts = np.array(list(map(np.array, jmp.search('[*].subtopics[*].count', new_structure))))
    old_sbt_counts = np.array(list(map(np.array, jmp.search('[*].subtopics[*].count', old_structure))))
    all_subtopic_counts = new_sbt_counts - old_sbt_counts

    # вытягиваем ссылки на подтемы
    subtopic_hrefs = jmp.search('[*].subtopics[*].href', new_structure)

    for topic_name, hrefs, subtopic_counts in zip(topic_names, subtopic_hrefs, all_subtopic_counts):
        problems = []
        new_problems = 0
        # проходимся по каждому блоку подзаданий в темах и смотрим только на прирост новых заданий
        for href, count in zip(hrefs, subtopic_counts):
            if count > 0:
                problems += get_problems(href, count)
                new_problems += count

        upd_structure.append({'topic': {'name': topic_name,
                                        'count': int(new_problems)},  # конвертируем в int,
                              'problems': problems                    # т.к. int32 из numpy не сериализуемый в JSON
                            })

    return upd_structure


def __create_topic_dict(topic: Tag) -> dict:
    """Поиск названий тем и количества заданий по ним"""

    # название каждой темы
    topic_name = topic.b.string
    # получаем количество заданий по данной теме; достаем -1 элемент,
    # т.к. в других количество заданий подтем
    problems_count = int(topic(class_='cat_count')[-1].string)
    topic_dict = {'name': topic_name,
                  'count': problems_count}
    return topic_dict


def __create_subtopic_list(topic: Tag) -> list:
    """
    Поиск названий подтем, количества заданий по каждой из них
    и ссылок для перехода к каждой подтеме
    """

    subtopics = []
    # получаем теги <a>, в каждом из которых есть название и ссылка на подтему
    subtopics_tags = topic.find_all(class_='cat_name', href=True)

    for subtopic_tag in subtopics_tags:
        # если нам попалась тема, а не подтема, то в ее
        # названии будут цифры и точка с пробелом после них
        if re.search(r'\d{1,2}\. ', subtopic_name := subtopic_tag.string):
            continue
        subtopic_dict = {'name': subtopic_name,
                         'href': subtopic_tag['href'].removeprefix('/') + '&sort=ids',
                         'count': int(subtopic_tag.next_sibling.string)}
        subtopics.append(subtopic_dict)

    return subtopics


def merge_added_problems(user: UserMixin, new_added_problems: list, new_structure: list) -> list:
    """Прибавление новых заданий"""
    
    added_problems = loads(user.added_problems)
    
    # считаем количество новых заданий по каждой теме
    new_counts = jmp.search('[*].topic.count', new_added_problems)
    
    # если новые задания появились перестраиваем старое дерево разности
    if any(new_counts):
        # вытягиваем списки новых проблем
        new_problems = jmp.search('[*].problems', new_added_problems)

        for count, problems, topic in zip(new_counts, new_problems, added_problems):
            # прибавляем (а НЕ переписываем!) количества заданий и сами задания
            topic['topic']['count'] += count
            topic['problems'] += problems

        kwargs = dict(indent=2, ensure_ascii=False)
        user.added_problems = dumps(added_problems, **kwargs)
        user.problems = dumps(new_structure, **kwargs)

    return added_problems