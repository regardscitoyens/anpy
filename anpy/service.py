# -*- coding: utf-8 -*-
from __future__ import division

import requests

from .parsing.amendement_parser import parse_amendements_summary
from .parsing.question_search_result_parser import parse_question_search_result

__all__ = ['AmendementSearchService', 'QuestionSearchService']


class AmendementSearchService(object):
    def __init__(self):
        self.base_url = "http://www2.assemblee-nationale.fr/recherche/query_amendements"
        self.default_params = {
            'texteRecherche': None,
            'numAmend': None,
            'idArticle': None,
            'idAuteur': None,
            'idDossierLegislatif': None,
            'idExamen': None,
            'idExamens': None,
            'periodeParlementaire': None,
            'dateDebut': None,
            'dateFin': None,
            'rows': 100,
            'start': None,
            'sort': None,
            'format': 'html',
            'tri': 'ordreTexteasc',
            'typeRes': 'liste',
            'typeDocument': 'amendement',
        }

    def get(self, **kwargs):
        """
        :param texteRecherche:
        :param numAmend:
        :param idArticle:
        :param idAuteur:
        :param idDossierLegislatif:
        :param idExamen:
        :param idExamens:
        :param periodeParlementaire:
        :param dateDebut:
        :param dateFin:
        :param rows:
        :param start:
        :param sort:
        """
        params = self.default_params.copy()
        params.update(kwargs)

        response = requests.get(self.base_url, params=params)

        return parse_amendements_summary(response.url, response.json())

    def total_count(self, **kwargs):
        response = self.get(rows=1, **kwargs)
        return response.total_count

    def iterator(self, rows=100, **kwargs):
        response = self.get(rows=rows, **kwargs)
        yield response

        for start in range(rows, response.total_count, rows):
            yield self.get(rows=rows, start=start + 1, **kwargs)

    def get_order(self, **kwargs):
        iterator = AmendementSearchService().iterator(**kwargs)
        order = []
        for it in iterator:
            order += [amendement.num_amend for amendement in it.results]
        return order


class QuestionSearchService(object):
    def __init__(self):
        self.base_url = 'http://www2.assemblee-nationale.fr/'
        self.search_url = '%srecherche/resultats_questions' % self.base_url
        self.default_params = {
            'limit': 10,
            'legislature': None,
            'replies[]': None,# ar, sr
            'removed[]': None,# 0,1
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

        params.update({'legislature': legislature, 'limit': size, 'replies[]': is_answered, 'removed[]': is_removed})
        response = requests.post(self.search_url, data=params)

        return parse_question_search_result(response.url, response.content)

    def total_count(self, legislature=14, is_answered=None, is_removed=None):
        return self.get(legislature=legislature, is_answered=is_answered, is_removed=is_removed, size=1).total_count

    def iter(self, legislature=14, is_answered=None, is_removed=None, size=10):
        search_results = self.get(legislature=legislature, is_answered=is_answered, is_removed=is_removed, size=size)
        yield search_results

        for start in range(1, search_results.total_count, size):
            if search_results.next_url is not None:
                yield parse_question_search_result(search_results.next_url, requests.get(self.base_url + search_results.next_url).content)