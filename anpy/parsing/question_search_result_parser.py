# -*- coding: utf-8 -*-

import re

from bs4 import BeautifulSoup


from ..model import QuestionSummary, QuestionSearchResult

__all__ = ['parse_question_search_result']


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
        legislature, numero, question_type = re.search('(\d+)-(\d+)(QE|QOSD)\.htm', url).groups()
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
    next_link = soup.find('div', class_='pagination-bootstrap').find_all('li')[-1]
    search_result.next_url = next_link.a['href'] if next_link.a else None

    return search_result