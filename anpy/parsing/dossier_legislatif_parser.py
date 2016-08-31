# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from future.utils import iteritems
from builtins import map, filter, str

import mistune
import re
from six.moves.urllib.parse import urljoin
from bs4 import BeautifulSoup
from operator import itemgetter
from html2text import html2text
from .date_utils import extract_datetime
from ..model import (
    ProcedureParlementaire,
    LegislativeAct,
    LegislativeStep,
    DecisionStatus)

__all__ = ['parse_dossier_legislatif']

AN_BASE_URL = 'http://www.assemblee-nationale.fr'


def parse_dossier_legislatif(url, html):
    soup = BeautifulSoup(clean_html(html), 'html5lib')
    tree = build_dossier_tree(soup)

    data = tree.extract_data()
    data['url'] = url

    return data


def build_dossier_tree(soup):
    root_node = DossierNode()
    current_node = root_node

    for element in filter(filter_dossier_element, soup.find_all(['p', 'h2'])):
        new_node_class = BaseNode.match_node_class(element)

        if new_node_class:
            parent = current_node.get_relevant_parent(new_node_class)
            current_node = new_node_class(parent=parent)
            parent.add_child(current_node)

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
                       EtudeImpactNode]:
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
        depot_loi_node = self.get_first_depot_loi_node()

        return {
            'title': self.extract_title(),
            'legislature': depot_loi_node.extract_legislature()
            if depot_loi_node else None,
            'procedure': depot_loi_node.extract_procedure()
            if depot_loi_node else None,
            'steps': [step.extract_data() for step in self.children],
        }

    def extract_title(self):
        if not self.elements:
            return

        return self.elements[0].text

    def get_first_depot_loi_node(self):
        depot_act_nodes = [
            child for step in self.children for child in step.children
            if isinstance(child, DepotLoiNode)]

        return depot_act_nodes[0] if depot_act_nodes else None


class LegislativeStepNode(BaseNode):
    steps_re = {
        LegislativeStep.AN_PREMIERE_LECTURE:
            re.compile('^assemblée nationale - 1ère lecture',
                       re.I | re.UNICODE),
        LegislativeStep.SENAT_PREMIERE_LECTURE:
            re.compile('^sénat - 1ère lecture',
                       re.I | re.UNICODE),
        LegislativeStep.AN_NOUVELLE_LECTURE:
            re.compile('^assemblée nationale - nouvelle lecture',
                       re.I | re.UNICODE),
        LegislativeStep.SENAT_NOUVELLE_LECTURE:
            re.compile('^sénat - nouvelle lecture',
                       re.I | re.UNICODE),
        LegislativeStep.AN_LECTURE_DEFINITIVE:
            re.compile('^assemblée nationale - lecture définitive',
                       re.I | re.UNICODE),
        LegislativeStep.CONSEIL_CONSTIT:
            re.compile('^conseil constitutionnel',
                       re.I | re.UNICODE),
        LegislativeStep.CMP:
            re.compile('^commission mixte paritaire \((accord|désaccord)?\)$',
                       re.I | re.UNICODE)
    }

    @classmethod
    def match(cls, html):
        return any(map(lambda r: r.match(html.text), cls.steps_re.values()))

    def get_relevant_parent(self, node_class):
        return self.parent if node_class == LegislativeStepNode else self

    def extract_data(self):
        return {
            'type': self.extract_type(),
            'acts': [child.extract_data() for child in self.children]
        }

    def extract_type(self):
        if not self.elements:
            return

        return next(
            map(itemgetter(0),
                filter(lambda item: item[1].match(self.elements[0].text),
                       iteritems(self.steps_re))))


class LegislativeActNode(BaseNode):
    regex = None

    @classmethod
    def match(cls, html):
        return cls.regex.match(html.text) if cls.regex else False

    def get_relevant_parent(self, node_class):
        return self.parent if issubclass(node_class, LegislativeActNode)\
            else self.parent.parent

    def extract_data(self):
        raise NotImplementedError


class ProcedureAccelereeNode(LegislativeActNode):
    regex = re.compile('^le gouvernement a engagé la procédure accélérée',
                       re.I | re.UNICODE)

    def extract_data(self):
        if not self.elements:
            return

        return {
            'type': LegislativeAct.PROCEDURE_ACCELEREE,
        }


class DepotLoiNode(LegislativeActNode):
    regex = re.compile('^(projet de loi|proposition de loi).+déposée? le',
                       re.I | re.UNICODE)

    @classmethod
    def match(cls, html):
        return cls.regex.match(html.text) and html.a if cls.regex else False

    def extract_data(self):
        if not self.elements:
            return

        return {
            'type': LegislativeAct.DEPOT_INITIATIVE,
            'url': self.extract_url(),
            'date': self.extract_date()
        }

    def extract_date(self):
        matched_dates = re.findall(' déposée? le (\d+ \w+ \d{4})',
                                   self.elements[0].text, re.UNICODE)

        return extract_datetime(matched_dates[0]) if matched_dates else None

    def extract_url(self):
        return urljoin(AN_BASE_URL, self.elements[0].a['href']) \
            if self.elements else None

    def extract_legislature(self):
        link = self.elements[0].a
        matched = re.match('/(\d{2})/', link['href'])

        if matched:
            return matched.group(1)

    def extract_procedure(self):
        if self.elements and 'Projet de loi' in self.elements[0].text:
            return ProcedureParlementaire.PJL
        elif self.elements and 'Proposition de loi' in self.elements[0].text:
            return ProcedureParlementaire.PPL


class DiscussionSeancePubliqueNode(LegislativeActNode):
    regex = re.compile('^discussion en séance publique', re.I | re.UNICODE)

    def extract_data(self):
        return {
            'type': LegislativeAct.DISCUSSION_SEANCE_PUBLIQUE,
            'seances': self.extract_seances(),
            'decision': self.extract_decision()
        }

    def extract_seances(self):
        return self.extract_seances_from_first_element() \
            if self.seances_in_first_element() \
            else self.extract_seances_from_all_elements()

    def seances_in_first_element(self):
        return 'au cours des séances' in self.elements[0].text

    def extract_seances_from_first_element(self):
        return [{'url': urljoin(AN_BASE_URL, a['href'])}
                for a in self.elements[0].find_all('a')]

    def extract_seances_from_all_elements(self):
        def extract_seance(element):
            return {
                'url': urljoin(AN_BASE_URL, element.a['href'])
                if element.a else None,
                'date': extract_datetime(element.text.split('séance du ')[1])
            }

        def filter_seance(element):
            return 'séance du ' in element.text and \
                   'Scrutin' not in element.text

        return list(map(extract_seance, filter(filter_seance, self.elements)))

    def extract_decision(self):
        last_element = next(filter(lambda e: 'de loi' in e.text and
                                             'Scrutin' not in e.text,
                                   self.elements))

        status = None
        if 'adopté' in last_element.text:
            status = DecisionStatus.ADOPTED
        elif 'modifié' in last_element.text:
            status = DecisionStatus.MODIFIED
        elif 'rejeté' in last_element.text:
            status = DecisionStatus.REJECTED

        matched_dates = re.findall(' le (\d+ \w+ \d{4})',
                                   last_element.text,
                                   re.I | re.UNICODE)

        return {
            'status': status,
            'date': extract_datetime(matched_dates[0])
            if matched_dates else None,
            'url': urljoin(AN_BASE_URL, last_element.a['href'])
            if last_element.a else None
        }


class AvisConseilEtatNode(LegislativeActNode):
    regex = re.compile('^avis du conseil d\'État', re.I | re.UNICODE)

    def extract_data(self):
        return {
            'type': LegislativeAct.AVIS_CONSEIL_ETAT,
            'url': urljoin(AN_BASE_URL, self.elements[0].a['href'])
        }


class EtudeImpactNode(LegislativeActNode):
    regex = re.compile('^etude d\'impact', re.I | re.UNICODE)

    def extract_data(self):
        return {
            'type': LegislativeAct.ETUDE_IMPACT,
            'url': urljoin(AN_BASE_URL, self.elements[0].a['href'])
        }
