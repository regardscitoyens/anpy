# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
from builtins import map, filter, str
from operator import itemgetter

import mistune
import requests
from bs4 import BeautifulSoup
from future.utils import iteritems
from html2text import html2text
from six.moves.urllib.parse import urljoin

from anpy.utils import extract_datetime

AN_BASE_URL = 'http://www.assemblee-nationale.fr'


class InvalidResponseException(Exception):
    pass


class Dossier(object):
    def __init__(self, url=None, senat_url=None, title=None,
                 legislature=None, procedure=None, steps=None):
        self.url = url
        self.senat_url = senat_url
        self.title = title
        self.legislature = legislature
        self.procedure = procedure
        self.steps = steps or []

    @staticmethod
    def download_and_build(url):
        resp = requests.get(url)
        if resp.status_code >= 400:
            raise InvalidResponseException('%s: %d' % (url, resp.status_code))
        return DossierParser(url, resp.content).parse()

    def to_dict(self):
        return {
            'url': self.url,
            'senat_url': self.senat_url,
            'title': self.title,
            'legislature': self.legislature,
            'procedure': self.procedure,
            'steps': self.steps
        }


class ProcedureParlementaire(object):
    PJL = 'PJL'
    PPL = 'PPL'


class LegislativeStepType(object):
    AN_PREMIERE_LECTURE = 'AN_PREMIERE_LECTURE'
    SENAT_PREMIERE_LECTURE = 'SENAT_PREMIERE_LECTURE'
    AN_DEUXIEME_LECTURE = 'AN_DEUXIEME_LECTURE'
    SENAT_DEUXIEME_LECTURE = 'SENAT_DEUXIEME_LECTURE'
    AN_TROISIEME_LECTURE = 'AN_TROISIEME_LECTURE'
    SENAT_TROISIEME_LECTURE = 'SENAT_TROISIEME_LECTURE'
    CMP = 'CMP'
    CONSEIL_CONSTIT = 'CONSEIL_CONSTITUT'
    AN_NOUVELLE_LECTURE = 'AN_NOUVELLE_LECTURE'
    SENAT_NOUVELLE_LECTURE = 'SENAT_NOUVELLE_LECTURE'
    AN_LECTURE_DEFINITIVE = 'AN_LECTURE_DEFINITIVE'


class DecisionStatus(object):
    ADOPTE = 'ADOPTE'
    REJETE = 'REJETE'
    MODIFIE = 'MODIFIE'


class LegislativeActType(object):
    ETUDE_IMPACT = 'ETUDE_IMPACT'
    AVIS_CONSEIL_ETAT = 'AVIS_CONSEIL_DETAT'
    PROCEDURE_ACCELEREE = 'PROCEDURE_ACCELEREE'
    REUNION_COMMISSION = 'REUNION_COMMISSION'
    DISCUSSION_COMMISSION = 'DISCUSSION_COMMISSION'
    TEXTE_COMMISSION = 'TEXTE_COMMISSION'
    DEPOT_RAPPORT = 'DEPOT_RAPPORT'
    SAISIE_COM_AVIS = 'SAISIE_COM_AVIS'
    NOMINATION_RAPPORTEURS = 'NOMINATION_RAPPORTEURS'
    DISCUSSION_SEANCE_PUBLIQUE = 'DISCUSSION_SEANCE_PUBLIQUE'
    DECISION = 'DECISION'
    DEPOT_INITIATIVE = 'DEPOT_INITIATIVE'
    SAISIE_COM_FOND = 'SAISIE_COM_FOND'
    PROMULGATION = 'PROMULGATION'
    SAISINE_CONSEIL_CONSTIT = 'SAISINE_CONSEIL_CONSTIT'


class DossierParser(object):
    def __init__(self, url, html):
        self.url = url
        self.html = html
        self.soup = BeautifulSoup(clean_html(html), 'html5lib')

    def parse(self):
        return Dossier(
            url=self.url,
            title=self.parse_title(),
            legislature=self.parse_legislature(self.url),
            procedure=self.parse_procedure(),
            steps=self.parse_steps(),
            senat_url=self.parse_senat_url())

    def parse_title(self):
        return self.soup.strong.text if self.soup.strong else None

    def parse_procedure(self):
        re_procedure = re.compile('(projet de loi|proposition de loi)', re.I)

        def match_procedure(a):
            return re_procedure.match(a.text)

        def get_procedure(a):
            proc = match_procedure(a).group(1).lower()
            if proc == 'projet de loi':
                return ProcedureParlementaire.PJL
            elif proc == 'proposition de loi':
                return ProcedureParlementaire.PPL

        return next(
            map(get_procedure,
                filter(match_procedure, self.soup.find_all('a'))), None)

    def parse_senat_url(self):
        re_url = re.compile('http://www.senat.fr/dossier-legislatif')
        re_url_alt = re.compile('http://www.senat.fr/dossierleg/')

        return next(
            filter(lambda url: re_url.match(url) or re_url_alt.match(url),
                   map(lambda a: a['href'], self.soup.find_all('a'))), None)

    def parse_legislature(self, url=None):
        re_legislature = re.compile(r'/(\d{2})/')

        def match_legislature(a):
            return re_legislature.match(a['href'])

        def get_matched_group(a):
            return match_legislature(a).group(1) \
                if match_legislature(a) else None

        if url and 'assemblee-nationale' in url:
            legislature = url.split('.fr/')[1].split('/')[0]
            if legislature:
                return legislature

        return next(map(get_matched_group,
                        filter(match_legislature, self.soup.find_all('a'))))

    def parse_steps(self):
        tree = self.build_step_tree()
        return tree.extract_data()

    def build_step_tree(self):
        root_node = DossierNode()
        current_node = root_node

        for element in filter(filter_dossier_element,
                              self.soup.find_all(['p', 'h2'])):
            new_node_class = BaseNode.match_node_class(element)

            if new_node_class:
                parent = current_node.get_relevant_parent(new_node_class)
                next_current_node = new_node_class(parent=parent)
                parent.add_child(next_current_node)
                current_node = next_current_node

            current_node.add_element(element)

        return root_node


def clean_html(html):
    soup = BeautifulSoup(html, 'html5lib')
    if soup.body.header:
        soup.body.header.extract()
    md_text = html2text(str(soup.body), bodywidth=0)
    return mistune.markdown(md_text).replace('<br>\n', '</p>\n<p>')


def filter_dossier_element(element):
    return element.text.strip() and \
           not element.text.startswith('_') and \
           not element.text.startswith('Accueil')


class BaseNode(object):
    def __init__(self, parent=None):
        self.parent = parent
        self.elements = []
        self.children = []

    @classmethod
    def match(cls, html):
        raise NotImplementedError

    @classmethod
    def match_node_class(cls, element):
        for class_ in [LegislativeStepNode,
                       DiscussionSeancePubliqueNode,
                       DepotLoiNode,
                       ProcedureAccelereeNode,
                       AvisConseilEtatNode,
                       EtudeImpactNode,
                       DepotTexteCommissionNode,
                       RapportNode,
                       DecisionNode]:
            if class_.match(element):
                return class_

    def get_relevant_parent(self, node_class):
        return self

    def add_child(self, node):
        self.children.append(node)

    def add_element(self, element):
        self.elements.append(element)

    def extract_data(self):
        raise NotImplementedError

    def __repr__(self):
        return '<%s [%s]>' % (
            self.__class__.__name__,
            self.elements[0].__repr__() if self.elements else '')


class DossierNode(BaseNode):
    def extract_data(self):
        return [step.extract_data() for step in self.children]


class LegislativeStepNode(BaseNode):
    steps_re = {
        LegislativeStepType.AN_PREMIERE_LECTURE:
            re.compile('^assemblée nationale - 1 ?ère lecture',
                       re.I | re.UNICODE),
        LegislativeStepType.SENAT_PREMIERE_LECTURE:
            re.compile('^sénat - 1 ?ère lecture',
                       re.I | re.UNICODE),
        LegislativeStepType.AN_DEUXIEME_LECTURE:
            re.compile('^assemblée nationale - 2 ?e lecture',
                       re.I | re.UNICODE),
        LegislativeStepType.SENAT_DEUXIEME_LECTURE:
            re.compile('^sénat - 2 ?e lecture',
                       re.I | re.UNICODE),
        LegislativeStepType.AN_TROISIEME_LECTURE:
            re.compile('^assemblée nationale - 3 ?e lecture',
                       re.I | re.UNICODE),
        LegislativeStepType.SENAT_TROISIEME_LECTURE:
            re.compile('^sénat - 3 ?e lecture',
                       re.I | re.UNICODE),
        LegislativeStepType.AN_NOUVELLE_LECTURE:
            re.compile('^assemblée nationale - nouvelle lecture',
                       re.I | re.UNICODE),
        LegislativeStepType.SENAT_NOUVELLE_LECTURE:
            re.compile('^sénat - nouvelle lecture',
                       re.I | re.UNICODE),
        LegislativeStepType.AN_LECTURE_DEFINITIVE:
            re.compile('^assemblée nationale - lecture définitive',
                       re.I | re.UNICODE),
        LegislativeStepType.CONSEIL_CONSTIT:
            re.compile('^conseil constitutionnel',
                       re.I | re.UNICODE),
        LegislativeStepType.CMP:
            re.compile(r'^commission mixte paritaire \((accord|désaccord)?\)$',
                       re.I | re.UNICODE)
    }

    @classmethod
    def match(cls, html):
        return any(map(lambda r: r.match(html.text), cls.steps_re.values()))

    def get_relevant_parent(self, node_class):
        return self.parent if node_class == LegislativeStepNode else self

    def extract_data(self):
        data = {
            'type': self.extract_type(),
            'acts': [act for child in self.children
                     for act in (child.extract_data() or [])]
        }

        if data['type'] == LegislativeStepType.CMP and self.elements:
            if 'Accord' in self.elements[0].text:
                data['status'] = 'ACCORD'
            if 'Désaccord' in self.elements[0].text:
                data['status'] = 'DESACCORD'

        return data

    def extract_type(self):
        if not self.elements:
            return

        return next(
            map(itemgetter(0),
                filter(lambda item: item[1].match(self.elements[0].text),
                       iteritems(self.steps_re))))


class LegislativeActNode(BaseNode):
    rule = None

    @classmethod
    def match(cls, html):
        return cls.rule.match(html.text) if cls.rule else False

    def get_relevant_parent(self, node_class):
        if self.parent.parent:
            return self.parent if issubclass(node_class, LegislativeActNode)\
                else self.parent.parent
        return self.parent

    def extract_data(self):
        raise NotImplementedError


class ProcedureAccelereeNode(LegislativeActNode):
    rule = re.compile('^le gouvernement a engagé la procédure accélérée',
                      re.I | re.UNICODE)

    def extract_data(self):
        if not self.elements:
            return

        matched_dates = re.findall(r' le (\d+\s?\w* \w+ \d{4})',
                                   self.elements[0].text,
                                   re.I | re.UNICODE)

        return [{
            'type': LegislativeActType.PROCEDURE_ACCELEREE,
            'date': extract_datetime(matched_dates[0])
            if matched_dates else None
        }]


class EtudeImpactNode(LegislativeActNode):
    rule = re.compile(r'^etude d\'impact', re.I | re.UNICODE)

    def extract_data(self):
        return [{
            'type': LegislativeActType.ETUDE_IMPACT,
            'url': urljoin(AN_BASE_URL, self.elements[0].a['href'])
        }]


class DepotLoiNode(LegislativeActNode):
    rule = re.compile('^(projet de loi|proposition de loi).+déposée? le',
                      re.I | re.UNICODE)

    @classmethod
    def match(cls, html):
        return cls.rule.match(html.text) and html.a if cls.rule else False

    def extract_data(self):
        if not self.elements:
            return

        return [{
            'type': LegislativeActType.DEPOT_INITIATIVE,
            'url': self.extract_url(),
            'date': self.extract_date()
        }]

    def extract_date(self):
        matched_dates = re.findall(r' déposée? le (\d+ \w+ \d{4})',
                                   self.elements[0].text, re.UNICODE)

        return extract_datetime(matched_dates[0]) if matched_dates else None

    def extract_url(self):
        return urljoin(AN_BASE_URL, self.elements[0].a['href']) \
            if self.elements else None

    def extract_legislature(self):
        link = self.elements[0].a
        matched = re.match(r'/(\d{2})/', link['href'])

        if matched:
            return matched.group(1)

    def extract_procedure(self):
        if self.elements and 'Projet de loi' in self.elements[0].text:
            return ProcedureParlementaire.PJL
        elif self.elements and 'Proposition de loi' in self.elements[0].text:
            return ProcedureParlementaire.PPL


class DepotTexteCommissionNode(LegislativeActNode):
    rule = re.compile('^texte de la commission.+(déposée?|mis en ligne) le',
                      re.I | re.UNICODE)

    @classmethod
    def match(cls, html):
        return cls.rule.match(html.text) and html.a if cls.rule else False

    def extract_data(self):
        if not self.elements:
            return

        return [{
            'type': LegislativeActType.TEXTE_COMMISSION,
            'url': self.extract_url(),
            'date': self.extract_date()
        }]

    def extract_date(self):
        matched_dates = re.findall(
            r'(?:déposée?|mis en ligne) le (\d+ \w+ \d{4})',
            self.elements[0].text, re.UNICODE)

        return extract_datetime(matched_dates[0]) if matched_dates else None

    def extract_url(self):
        return urljoin(AN_BASE_URL, self.elements[0].a['href']) \
            if self.elements else None


class RapportNode(LegislativeActNode):
    rule = re.compile('^rapport.+déposée? le',
                      re.I | re.UNICODE)

    @classmethod
    def match(cls, html):
        return cls.rule.match(html.text) and html.a if cls.rule else False

    def extract_data(self):
        if not self.elements:
            return

        return [{
            'type': LegislativeActType.DEPOT_RAPPORT,
            'url': self.extract_url(),
            'date': self.extract_date()
        }]

    def extract_date(self):
        matched_dates = re.findall(r' déposée? le (\d+ \w+ \d{4})',
                                   self.elements[0].text, re.UNICODE)

        return extract_datetime(matched_dates[0]) if matched_dates else None

    def extract_url(self):
        return urljoin(AN_BASE_URL, self.elements[0].a['href']) \
            if self.elements else None


class DecisionNode(LegislativeActNode):
    rule = re.compile('^(projet de loi|proposition de loi)(?!.*déposé)',
                      re.I | re.UNICODE)

    def extract_data(self):
        status = None
        if 'adopté' in self.elements[0].text:
            status = DecisionStatus.ADOPTE
        elif 'modifié' in self.elements[0].text:
            status = DecisionStatus.MODIFIE
        elif 'rejeté' in self.elements[0].text:
            status = DecisionStatus.REJETE

        matched_dates = re.findall(r' le (\d+\s?\w* \w+ \d{4})',
                                   self.elements[0].text,
                                   re.I | re.UNICODE)

        return [{
            'type': LegislativeActType.DECISION,
            'status': status,
            'date': extract_datetime(matched_dates[0])
            if matched_dates else None,
            'url': urljoin(AN_BASE_URL, self.elements[0].a['href'])
            if self.elements[0].a else None
        }]


class DiscussionSeancePubliqueNode(LegislativeActNode):
    rule = re.compile('^discussion en séance publique', re.I | re.UNICODE)

    def extract_data(self):
        return self.extract_seances_from_first_element() \
            if self.seances_in_first_element() \
            else self.extract_seances_from_all_elements()

    def seances_in_first_element(self):
        return 'au cours des séances' in self.elements[0].text

    def extract_seances_from_first_element(self):
        return [{'url': urljoin(AN_BASE_URL, a['href']),
                 'type': LegislativeActType.DISCUSSION_SEANCE_PUBLIQUE}
                for a in self.elements[0].find_all('a')]

    def extract_seances_from_all_elements(self):
        def extract_seance(element):
            return {
                'url': urljoin(AN_BASE_URL, element.a['href'])
                if element.a else None,
                'date': extract_datetime(element.text.split('séance du ')[1]),
                'type': LegislativeActType.DISCUSSION_SEANCE_PUBLIQUE
            }

        def filter_seance(element):
            return 'séance du ' in element.text and \
                   'Scrutin' not in element.text

        return list(map(extract_seance, filter(filter_seance, self.elements)))


class AvisConseilEtatNode(LegislativeActNode):
    rule = re.compile(r'^avis du conseil d\'État', re.I | re.UNICODE)

    def extract_data(self):
        if not self.elements[0].a:
            return
        return [{
            'type': LegislativeActType.AVIS_CONSEIL_ETAT,
            'url': urljoin(AN_BASE_URL, self.elements[0].a['href'])
        }]
