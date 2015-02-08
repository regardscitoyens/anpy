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

    def _get(self, **kwargs):
        params = self.default_params.copy()
        params.update(kwargs)
        response = requests.get(self.base_url, params=params)
        return response

    def get(self, texteRecherche=None, numAmend=None, idArticle=None, idAuteur=None, idDossierLegislatif=None,
            idExamen=None, periodeParlementaire=None, dateDebut=None, dateFin=None, rows=100, start=None, sort=None):
        response = self._get(
            texteRecherche=texteRecherche, numAmend=numAmend, idArticle=idArticle, idAuteur=idAuteur,
            idDossierLegislatif=idDossierLegislatif, idExamen=idExamen, periodeParlementaire=periodeParlementaire,
            dateDebut=dateDebut, dateFin=dateFin, rows=rows, start=start, sort=sort)
        return parse_amendements_summary(response.url, response.json())

    def total_count(self, **kwargs):
        # First get total number of pages
        response = self.get(**kwargs)
        return response.total_count

    def iter(self, rows=100, **kwargs):
        # First get total number of pages
        response = self.get(rows=1, **kwargs)
        import pdb
        pdb.set_trace()

        for start in range(0, response.total_count, rows):
            yield self.get(rows=rows, **kwargs)

    def get_order(self, **kwargs):
        iterator = AmendementSearchService().iter(**kwargs)
        order = []
        for result in iterator:
            order += [amendement.num_amend for amendement in self.get(**kwargs).results]
        return order


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
