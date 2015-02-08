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
            'typeDocument': 'amendement',
            'rows': 100,
            'format': 'html',
            'tri': 'ordreTextedesc',
            'typeRes': 'liste',
            'idArticle': None,
            'idAuteur': None,
            'numAmend': None,
            'idDossierLegislatif': None,
            'idExamen': None,
            'sort': None,
            'dateDebut': None,
            'dateFin': None,
            'periodeParlementaire': None,
            'texteRecherche': None,
            'start': None,
        }

    def _get(self, **kwargs):
        params = self.default_params.copy()
        params.update(kwargs)
        return requests.get(self.base_url, params=params)

    def get(self, start_date=None, end_date=None, numero=None, size=100, start=None):
        # FIXME : do we really want to rewrite parameters' names ?
        response = self._get(dateDebut=start_date, dateFin=end_date, numAmend=numero, rows=size, start=start)
        return parse_amendements_summary(response.url, response.json())

    def total_count(self, start_date=None, end_date=None, numero=None):
        # First get total number of pages
        response = self.get(start_date=start_date, end_date=end_date, numero=numero, size=1)
        return response.total_count

    def iter(self, start_date, end_date=None, numero=None, size=100):
        # First get total number of pages
        response = self.get(start_date, end_date=end_date, numero=numero, size=1)

        for start in range(0, response.total_count, size):
            yield self.get(start_date, end_date=end_date, numero=numero, size=size, start=start)

    def get_order(self, id_dossier, id_examen):
        return [amendement.num_amtxt for amendement in self._get(idDossier=id_dossier, idExamen=id_examen).results]


class QuestionSearchService(object):
    def __init__(self):
        self.base_url = "http://www2.assemblee-nationale.fr/recherche/resultats_questions"
        self.default_params = {
            'limit': 10,
            'legislature': None,
            'replies[]': None, # ar, sr
            'removed[]': None, # 0,1
            'ssTypeDocument[]': 'qe',
        }

    def _get(self, legislature=14, is_answered=None, is_removed=None, size=10):
        params = self.default_params.copy()

        if is_answered:
            is_answered = 'ar'
        elif is_answered is not None:
            is_answered = 'sr'
        if is_removed is not None:
            is_removed = int(is_removed)

        params.update({'legislature': legislature, 'limit': size, 'replies[]': is_answered, 'removed[]': is_removed})

        return requests.post(self.base_url, data=params)

    def get(self, legislature=14, is_answered=None, is_removed=None, size=10):
        response = self._get(legislature=legislature, is_answered=is_answered, is_removed=is_removed, size=size)
        return parse_question_search_result(response.url, response.content)

    def total_count(self, legislature=14, is_answered=None, is_removed=None):
        return self.get(legislature=legislature, is_answered=is_answered, is_removed=is_removed, size=1).total_count

    @staticmethod
    def _get_next(next_url):
        next_url = "http://www2.assemblee-nationale.fr" + next_url
        return parse_question_search_result(next_url, requests.get(next_url).content)

    def iter(self, legislature=14, is_answered=None, is_removed=None, size=10):
        # First get total number of pages
        search_results = self.get(legislature=legislature, is_answered=is_answered, is_removed=is_removed, size=size)
        yield search_results

        for start in range(1, search_results.total_count, size):
            if search_results.next_url is not None:
                search_results = self._get_next(search_results.next_url)
                yield search_results
