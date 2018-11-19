# -*- coding: utf-8 -*-

import logging
import re
import time

import attr
import requests
from bs4 import BeautifulSoup, NavigableString, Comment

from anpy.utils import convert_camelcase_to_underscore

LOGGER = logging.getLogger(__name__)


def parse_amendements_summary(url, json_response):
    """
    json schema :
    {
      infoGenerales: {
        nb_resultats, debut, nb_docs
      },
      data_table: 'id|numInit|titreDossierLegislatif|urlDossierLegislatif|'
                  'instance|numAmend|urlAmend|designationArticle|'
                  'designationAlinea|dateDepot|signataires|sort'
    }

    NB : the json response does not contain the dispositif and expose, that's
    why we call it "amendement's summary"
    """

    amendements = []
    fields = [convert_camelcase_to_underscore(field) for field in
              json_response['infoGenerales']['description_schema'].split('|')]

    for row in json_response['data_table']:
        values = row.split('|')
        amd = AmendementSummary(**dict(zip(fields, values)))
        amd.legislature = re.search(r'www.assemblee-nationale.fr/(\d+)/',
                                    amd.url_amend).groups()[0]
        amendements.append(amd)

    return AmendementSearchResult(**{
        'url': url,
        'total_count': json_response['infoGenerales']['nb_resultats'],
        'start': json_response['infoGenerales']['debut'],
        'size': json_response['infoGenerales']['nb_docs'],
        'results': amendements
    })


def parse_amendement(url, html_response):
    soup = BeautifulSoup(html_response, "html5lib")

    meta_names = [
        'NUM_AMTXT', 'NUM_AMEND', 'AMEND_PARENT', 'URL_DOSSIER', 'NUM_INIT',
        'ETAPE', 'DELIBERATION', 'TITRE_INIT', 'NUM_PARTIE',
        'DESIGNATION_ARTICLE', 'URL_DIVISION', 'DESIGNATION_ALINEA', 'MISSION',
        'AUTEURS', 'AUTEUR_ID', 'GROUPE_ID', 'COSIGNATAIRES_ID', 'SEANCE',
        'SORT', 'DATE_BADAGE', 'DATE_SORT', 'ORDRE_TEXTE', 'CODE', 'REFCODE',
        'LEGISLATURE',
    ]

    kwargs = dict((meta_name.lower(), clean_text(soup.find(
        'meta', attrs={'name': meta_name})['content']))
        for meta_name in meta_names)
    kwargs['auteurs'] = kwargs['auteurs'].replace(u'\xa0', ' ')
    kwargs['dispositif'] = clean_text(remove_inline_css_and_invalid_tags(
        soup.find('dispositif')))
    kwargs['expose'] = clean_text(remove_inline_css_and_invalid_tags(
        soup.find('expose')))
    kwargs['url'] = url

    return Amendement(**kwargs)


class AmendementSearchService(object):
    def __init__(self):
        self.base_url = "http://www2.assemblee-nationale.fr/recherche/query_amendements"  # noqa
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

        start = time.time()
        response = requests.get(self.base_url, params=params)
        end = time.time()

        LOGGER.debug(
            'fetched amendements with search params: %s in %0.2f s',
            params,
            end - start
        )

        return parse_amendements_summary(response.url, response.json())

    def total_count(self, **kwargs):
        kwargs_copy = kwargs.copy()
        kwargs_copy['rows'] = 1
        response = self.get(**kwargs_copy)
        return response.total_count

    def iterator(self, **kwargs):
        rows = kwargs.get('rows', self.default_params['rows'])

        response = self.get(**kwargs)

        LOGGER.debug('start to fetch %s amendements with page size of %s',
                     response.total_count,
                     rows)
        LOGGER.debug('amendements fetched: %s / %s (%.1f%%)',
                     rows,
                     response.total_count,
                     rows / response.total_count * 100)

        yield response

        for start in range(rows, response.total_count, rows):
            LOGGER.debug('amendements fetched: %s / %s (%.1f%%)',
                         rows + start,
                         response.total_count,
                         (rows + start) / response.total_count * 100)
            kwargs_copy = kwargs.copy()
            kwargs_copy['start'] = start + 1
            yield self.get(**kwargs_copy)

    def get_order(self, **kwargs):
        iterator = AmendementSearchService().iterator(**kwargs)
        order = []
        for it in iterator:
            order += [amendement.num_amend for amendement in it.results]
        return order


@attr.s
class AmendementSearchResult(object):
    url = attr.ib(default=None)
    total_count = attr.ib(default=None)
    start = attr.ib(default=None)
    size = attr.ib(default=None)
    results = attr.ib(default=None)


@attr.s
class AmendementSummary(object):
    id = attr.ib(default=None)
    num_init = attr.ib(default=None)
    titre_dossier_legislatif = attr.ib(default=None)
    url_dossier_legislatif = attr.ib(default=None)
    instance = attr.ib(default=None)
    num_amend = attr.ib(default=None)
    url_amend = attr.ib(default=None)
    designation_article = attr.ib(default=None)
    designation_alinea = attr.ib(default=None)
    date_depot = attr.ib(default=None)
    signataires = attr.ib(default=None)
    sort = attr.ib(default=None)
    legislature = attr.ib(default=None)
    mission_visee = attr.ib(default=None)
    sous_reserve_de_traitement = attr.ib(default=None)


@attr.s
class Amendement(object):
    url = attr.ib(default=None)
    num_amtxt = attr.ib(default=None)
    amend_parent = attr.ib(default=None)
    url_dossier = attr.ib(default=None)
    num_init = attr.ib(default=None)
    etape = attr.ib(default=None)
    deliberation = attr.ib(default=None)
    titre_init = attr.ib(default=None)
    num_partie = attr.ib(default=None)
    designation_article = attr.ib(default=None)
    url_division = attr.ib(default=None)
    designation_alinea = attr.ib(default=None)
    mission = attr.ib(default=None)
    auteurs = attr.ib(default=None)
    auteur_id = attr.ib(default=None)
    groupe_id = attr.ib(default=None)
    cosignataires_id = attr.ib(default=None)
    seance = attr.ib(default=None)
    sort = attr.ib(default=None)
    date_badage = attr.ib(default=None)
    date_sort = attr.ib(default=None)
    ordre_texte = attr.ib(default=None)
    code = attr.ib(default=None)
    refcode = attr.ib(default=None)
    legislature = attr.ib(default=None)
    dispositif = attr.ib(default=None)
    expose = attr.ib(default=None)
    num_amend = attr.ib(default=None)

    @staticmethod
    def download_and_build(url):
        return parse_amendement(url, requests.get(url).content)


def clean_text(text):
    return text.strip().replace('\n', '').replace(u'\u2019', '\'')


def remove_inline_css_and_invalid_tags(soup):
    if soup is None:
        return u''

    if soup.div:
        soup = soup.div

    for invalid_tag in ['b', 'i', 'u']:
        for match in soup.findAll(invalid_tag):
            match.unwrap()

    # remove comments
    [comment.extract() for comment in
        soup.findAll(text=lambda text: isinstance(text, Comment))]

    for tag in soup:
        if type(tag) != NavigableString:
            del tag["style"]
            del tag["class"]

    return soup.decode_contents()
