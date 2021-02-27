from requests import get, Response
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


url = 'https://inf-ege.sdamgia.ru/'


def get_response(page: str) -> Response:
    """Подключение к сайту решу егэ"""
    # многие сайты при большом количестве попыток подключения парсера
    # блокируют его, поэтому мы передаем им рандомный фейковый user_agent
    # каждый раз, когда подключаемся к сайту
    user_agent = UserAgent().random
    headers = {'user_agent': user_agent}

    response = get(url + page, headers=headers)
    return response


def get_catalog() -> list:
    """"Парсинг каталога заданий со страницы с ними"""

    catalog_page = 'prob_catalog'
    response = get_response(catalog_page)
    soup = BeautifulSoup(response.content, 'lxml')
    # каждая тема в каталоге находится в теге <div class="cat_category"></div>, у которого нет атрибута data-sort
    # если парсить с data-sort!=False, то получим ненужные теги; парсим с 1 элемента, т.к. в 0 не то, что нам нужно
    catalog = soup('div', {'class': 'cat_category', 'data-sort': False})[1:]
    return catalog

    
def get_problems(problems_page: str, dif_count: int) -> list:
    """Парсинг новых заданий в подтеме"""

    response = get_response(problems_page)
    soup = BeautifulSoup(response.content, 'lxml')

    # выбираем последние dif_count новых заданий, парсим их id и оставляем относительные пути к ним
    problems = [{'id': (id := problem['id'].removeprefix('problem_')), 'href': f'problem?id={id}'}
                for problem in soup('div', {'class': 'problem_container'})[:dif_count]]
    return problems