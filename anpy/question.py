# -*- coding: utf-8 -*-
import re

import attr
import requests
import xmltodict
from bs4 import BeautifulSoup


def parse_question(url, xml):
    data = xmltodict.parse(xml)['QUESTION']
    data['URL'] = url
    return data


def parse_question_search_result(url, html_content):
    soup = BeautifulSoup(html_content, "html5lib")

    search_result = QuestionSearchResult(**{
        'url': url,
        'total_count': int(soup.find('article').div.div.p.strong.text)
    })

    results = []
    for tr in soup.find_all('tr')[1:]:
        all_tds = tr.find_all('td')
        url = all_tds[0].a['href']
        legislature, numero, question_type = re.search(
            r'(\d+)-(\d+)(QE|QOSD)\.htm', url).groups()
        dates = all_tds[2].find_all('strong')
        results.append(QuestionSummary(**{
            'url': url,
            'legislature': legislature,
            'numero': numero,
            'question_type': question_type,
            'author': all_tds[1].strong.text,
            'tags': all_tds[1].em.text,
            'publication_date': dates[0].text,
            'answer_date': dates[1].text if len(dates) > 1 else None,
        }))

    search_result.results = results
    next_link = soup.find('div',
                          class_='pagination-bootstrap').find_all('li')[-1]
    search_result.next_url = next_link.a['href'] if next_link.a else None

    return search_result


class QuestionSearchService(object):
    def __init__(self):
        self.base_url = 'http://www2.assemblee-nationale.fr/'
        self.search_url = '%srecherche/resultats_questions' % self.base_url
        self.default_params = {
            'limit': 10,
            'legislature': None,
            'replies[]': None,  # ar, sr
            'removed[]': None,  # 0,1
            'ssTypeDocument[]': 'qe',
        }

    def get(self, legislature=14, is_answered=None, is_removed=None, size=10):
        params = self.default_params.copy()

        if is_answered:
            is_answered = 'ar'
        elif is_answered is not None:
            is_answered = 'sr'
        if is_removed is not None:
            is_removed = int(is_removed)

        params.update({
            'legislature': legislature,
            'limit': size,
            'replies[]': is_answered,
            'removed[]': is_removed
        })
        response = requests.post(self.search_url, data=params)

        return parse_question_search_result(response.url, response.content)

    def total_count(self, legislature=14, is_answered=None, is_removed=None):
        return self.get(legislature=legislature, is_answered=is_answered,
                        is_removed=is_removed, size=1).total_count

    def iter(self, legislature=14, is_answered=None, is_removed=None, size=10):
        search_results = self.get(legislature=legislature,
                                  is_answered=is_answered,
                                  is_removed=is_removed, size=size)
        yield search_results

        for start in range(1, search_results.total_count, size):
            if search_results.next_url is not None:
                yield parse_question_search_result(
                    search_results.next_url,
                    requests.get(self.base_url +
                                 search_results.next_url).content)


@attr.s
class QuestionSearchResult(object):
    url = attr.ib(default=None)
    total_count = attr.ib(default=None)
    next_url = attr.ib(default=None)
    size = attr.ib(default=None)
    results = attr.ib(default=None)


@attr.s
class QuestionSummary(object):
    url = attr.ib(default=None)
    legislature = attr.ib(default=None)
    numero = attr.ib(default=None)
    question_type = attr.ib(default=None)
    author = attr.ib(default=None)
    tags = attr.ib(default=None)
    publication_date = attr.ib(default=None)
    answer_date = attr.ib(default=None)
