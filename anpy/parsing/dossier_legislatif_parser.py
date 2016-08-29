# -*- coding: utf-8 -*-

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


def parse_dossier_legislatif(url, html_response):
    dossier = DossierParser.parse(
        BeautifulSoup(clean_html(html_response), 'html5lib'))

    data = dossier.extract_data()
    data['url'] = url

    return data


def clean_html(html):
    soup = BeautifulSoup(html, "html5lib")
    if soup.body.header:
        soup.body.header.extract()
    md_text = html2text(str(soup.body), bodywidth=0)
    return mistune.markdown(md_text).replace('<br>\n', '</p>\n<p>')


class DossierParser(object):
    def __init__(self):
        pass

    @classmethod
    def find_node_class(cls, element):
        for class_ in [LegislativeStepNode, LegislativeActNode, DepotLoiNode,
                       DiscussionSeancePubliqueNode,
                       AvisConseilEtatNode, EtudeImpactNode]:
            if class_.match(element):
                return class_

    @classmethod
    def parse(cls, html):
        root_node = DossierNode()
        current_node = root_node

        for element in filter(cls.filter_element, html.find_all(['p', 'h2'])):
            if cls.find_node_class(element):
                parent = current_node.get_relevant_parent(
                    cls.find_node_class(element))
                current_node = cls.find_node_class(element)(parent=parent)
                parent.add_child(current_node)

            current_node.add_element(element)

        return root_node

    @classmethod
    def filter_element(cls, element):
        return element.text.strip() and \
               element.text not in ['_', 'Accueil > Dossiers']


class BaseNode(object):
    def __init__(self, parent=None):
        self.parent = parent
        self.elements = []
        self.children = []

    def get_ascendancy(self):
        if self.parent is None:
            return []

        return [self.parent] + self.parent.get_ascendancy()

    def get_relevant_parent(self, node_class):
        def extract_main_class(node):
            if issubclass(node.__class__, LegislativeActNode):
                return LegislativeActNode

            return node.__class__

        matched = [node for node in [self] + self.get_ascendancy()
                   if issubclass(node_class, extract_main_class(node))]
        return matched[0].parent \
            if matched else self

    def add_child(self, node):
        assert issubclass(node.__class__, BaseNode)
        self.children.append(node)

    def add_element(self, element):
        self.elements.append(element)

    @classmethod
    def match(cls, html):
        return True

    def extract_data(self):
        raise NotImplementedError

    def __repr__(self):
        return '<%s [%s]>' % (
            self.__class__.__name__,
            self.elements[0].__repr__() if self.elements else '')


class DossierNode(BaseNode):
    def extract_data(self):
        steps = self.get_steps()

        if not steps:
            return

        return {
            'title': self.extract_title(),
            'legislature': steps[0].children[0].extract_legislature()
            if steps[0].children else None,
            'procedure': steps[0].children[0].extract_procedure()
            if steps[0].children else None,
            'steps': [step.extract_data() for step in steps],
        }

    def extract_title(self):
        if not self.elements:
            return

        return self.elements[0].text

    def get_steps(self):
        return [child for child in self.children
                if isinstance(child, LegislativeStepNode)]


class LegislativeStepNode(BaseNode):
    steps_re = {
        LegislativeStep.AN_PREMIERE_LECTURE:
            re.compile('^Assemblée nationale - 1ère lecture'),
        LegislativeStep.SENAT_PREMIERE_LECTURE:
            re.compile('^Sénat - 1ère lecture'),
        LegislativeStep.AN_NOUVELLE_LECTURE:
            re.compile('^Assemblée nationale - Nouvelle lecture'),
        LegislativeStep.SENAT_NOUVELLE_LECTURE:
            re.compile('^Sénat - Nouvelle lecture'),
        LegislativeStep.AN_LECTURE_DEFINITIVE:
            re.compile('^Assemblée nationale - Lecture définitive'),
        LegislativeStep.CONSEIL_CONSTIT:
            re.compile('^conseil constitutionnel', re.I),
        LegislativeStep.CMP:
            re.compile('^commission mixte paritaire \((Accord|Désaccord)?\)$',
                       re.I)
    }

    @classmethod
    def match(cls, html):
        return any(map(lambda r: r.match(html.text), cls.steps_re.values()))

    def extract_data(self):
        return {
            'type': self.extract_type(),
            'acts': [child.extract_data() for child in self.children
                     if issubclass(child.__class__, LegislativeActNode)]
        }

    def extract_type(self):
        if not self.elements:
            return

        return next(
            map(itemgetter(0),
                filter(lambda item: item[1].match(self.elements[0].text),
                       self.steps_re.items())))


class LegislativeActNode(BaseNode):
    act_re = {
        LegislativeAct.PROCEDURE_ACCELEREE:
            re.compile('Le Gouvernement a engagé la procédure accéléré', re.I)
    }

    def __init__(self, parent=None):
        super(LegislativeActNode, self).__init__(parent)

    @classmethod
    def match(cls, html):
        return any(map(lambda r: r.match(html.text), cls.act_re.values()))

    def extract_data(self):
        return {
            'type': self.extract_type()
        }

    def extract_type(self):
        if not self.elements:
            return

        return next(
            map(itemgetter(0),
                filter(lambda item: item[1].match(self.elements[0].text),
                       self.act_re.items())))


class DepotLoiNode(LegislativeActNode):
    regex = re.compile('^(Projet de loi|Proposition de loi).+déposée? le .*')

    @classmethod
    def match(cls, html):
        return cls.regex.match(html.text) and html.a

    def extract_data(self):
        if not self.elements:
            return

        matched_dates = re.findall(' déposée? le (\d+ \w+ \d{4})',
                                   self.elements[0].text)

        return {
            'type': LegislativeAct.DEPOT_INITIATIVE,
            'url': urljoin(AN_BASE_URL, self.elements[0].a['href']),
            'date': extract_datetime(matched_dates[0])
            if matched_dates else None
        }

    def extract_type(self):
        return LegislativeAct.DEPOT_INITIATIVE

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
    regex = re.compile('^Discussion en séance publique')

    @classmethod
    def match(cls, html):
        return cls.regex.match(html.text)

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

        matched_dates = re.findall(' le (\d+ \w+ \d{4})', last_element.text)

        return {
            'status': status,
            'date': extract_datetime(matched_dates[0])
            if matched_dates else None,
            'url': urljoin(AN_BASE_URL, last_element.a['href'])
            if last_element.a else None
        }

    def extract_type(self):
        return LegislativeAct.DISCUSSION_SEANCE_PUBLIQUE


class AvisConseilEtatNode(LegislativeActNode):
    regex = re.compile('^avis du conseil d\'État', re.I)

    @classmethod
    def match(cls, html):
        return cls.regex.match(html.text)

    def extract_data(self):
        return {
            'type': LegislativeAct.AVIS_CONSEIL_ETAT,
            'url': urljoin(AN_BASE_URL, self.elements[0].a['href'])
        }

    def extract_type(self):
        return LegislativeAct.AVIS_CONSEIL_ETAT


class EtudeImpactNode(LegislativeActNode):
    regex = re.compile('^Etude d\'impact', re.I)

    @classmethod
    def match(cls, html):
        return cls.regex.match(html.text)

    def extract_data(self):
        return {
            'type': LegislativeAct.ETUDE_IMPACT,
            'url': urljoin(AN_BASE_URL, self.elements[0].a['href'])
        }

    def extract_type(self):
        return LegislativeAct.ETUDE_IMPACT
