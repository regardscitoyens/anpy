# -*- coding: utf-8 -*-

import re

from bs4 import BeautifulSoup, NavigableString

from ..model import AmendementSummary, Amendement, AmendementSearchResult


def convert_camelcase_to_underscore(name):
    # thx to http://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-camel-case
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def parse_amendements_summary(url, json_response):
    """
    json schema :
    {
      infoGenerales: {
        nb_resultats, debut, nb_docs
      },
      data_table: 'id|numInit|titreDossierLegislatif|urlDossierLegislatif|instance|numAmend|urlAmend|designationArticle|designationAlinea|dateDepot|signataires|sort'
    }

    NB : the json response does not contain the dispositif and expose, that's why we call it "amendement's summary"
    """

    amendements = []
    fields = [convert_camelcase_to_underscore(field) for field in json_response['infoGenerales']['description_schema'].split('|')]

    for row in json_response['data_table']:
        values = row.split('|')
        amd = AmendementSummary(**dict(zip(fields, values)))
        amd.legislature = re.search('www.assemblee-nationale.fr/(\d+)/', amd.url_amend).groups()[0]
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
        'NUM_AMTXT', 'NUM_AMEND', 'AMEND_PARENT', 'URL_DOSSIER', 'NUM_INIT', 'ETAPE', 'DELIBERATION', 'TITRE_INIT', 'NUM_PARTIE',
        'DESIGNATION_ARTICLE', 'URL_DIVISION', 'DESIGNATION_ALINEA', 'MISSION', 'AUTEURS', 'AUTEUR_ID', 'GROUPE_ID',
        'COSIGNATAIRES_ID', 'SEANCE', 'SORT', 'DATE_BADAGE', 'DATE_SORT', 'ORDRE_TEXTE', 'CODE', 'REFCODE',
        'LEGISLATURE',
    ]

    kwargs = dict((meta_name.lower(), clean_text(soup.find('meta', attrs={'name': meta_name})['content'])) for meta_name in meta_names)
    kwargs['auteurs'] = kwargs['auteurs'].replace(u'\xa0', ' ')
    kwargs['dispositif'] = clean_text(remove_inline_css_and_invalid_tags(soup.find('dispositif')))
    kwargs['expose'] = clean_text(remove_inline_css_and_invalid_tags(soup.find('expose')))
    kwargs['url'] = url

    return Amendement(**kwargs)


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

    for tag in soup:
        if type(tag) != NavigableString:
            del tag["style"]
            del tag["class"]

    return soup.decode_contents()

