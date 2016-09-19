# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
from builtins import filter, str

import requests
from bs4 import BeautifulSoup

from .utils import extract_datetime


class Scrutin(object):
    def __init__(self, url=None, title=None, legislature=None, numero=None,
                 date=None, synthese=None, groupes=[]):
        self.url = url
        self.title = title
        self.legislature = legislature
        self.numero = numero
        self.date = date
        self.synthese = synthese
        self.groupes = groupes

    @staticmethod
    def download_and_build(url):
        return ScrutinParser(url, requests.get(url).content).parse()

    def to_dict(self):
        return {
            'url': self.url,
            'title': self.title,
            'legislature': self.legislature,
            'numero': self.numero,
            'date': self.date,
            'synthese': self.synthese.to_dict() if self.synthese else {},
            'groupes': {g.groupe: g.to_dict() for g in self.groupes}
        }


class ScrutinSynthese(object):
    ADOPTE = 'adopté'
    REJETE = 'rejeté'

    def __init__(self, votants=None, exprimes=None, majorite_absolue=None,
                 pour=None, contre=None, resultat=None):
        self.votants = votants
        self.exprimes = exprimes
        self.majorite_absolue = majorite_absolue
        self.pour = pour
        self.contre = contre
        self.resultat = resultat

    @staticmethod
    def build(url, html):
        return ScrutinSyntheseParser(url, html).parse()

    def to_dict(self):
        return {
            'votants': self.votants,
            'exprimes': self.exprimes,
            'majorite_absolue': self.majorite_absolue,
            'pour': self.pour,
            'contre': self.contre,
            'resultat': self.resultat
        }


class ScrutinGroupe(object):
    VOTE_POUR = 'pour'
    VOTE_CONTRE = 'contre'
    VOTE_ABSTENTION = 'abstention'
    VOTE_NON_VOTANT = 'non-votant'

    def __init__(self, groupe=None, pour=[], contre=[], abstention=[],
                 nonvotants=[]):
        self.groupe = groupe
        self.pour = pour
        self.contre = contre
        self.abstention = abstention
        self.nonvotants = nonvotants

    @staticmethod
    def build(url, soup):
        return ScrutinGroupeParser(url, soup).parse()

    def to_dict(self):
        return {
            'pour': self.pour,
            'contre': self.contre,
            'abstention': self.abstention,
            'non-votants': self.nonvotants
        }


class ScrutinParser(object):
    RE_DATE = re.compile(r'(\d+/\d+/\d+)')
    RE_SCRUTIN_URL = re.compile(
        r'/scrutins/detail/\(legislature\)/(\d+)/\(num\)/(\d+)')

    def __init__(self, url, html):
        self.url = url
        self.html = html
        self.soup = BeautifulSoup(html, 'html5lib')

    def parse(self):
        return Scrutin(
            url=self.url,
            title=self.parse_title(),
            legislature=self.parse_legislature(),
            numero=self.parse_numero(),
            date=self.parse_date(),
            synthese=ScrutinSynthese.build(self.url, self.html),
            groupes=self.parse_groupes()
        )

    def parse_title(self):
        return self.soup.h3.text if self.soup.h3 else None

    def parse_legislature(self):
        m = self.RE_SCRUTIN_URL.search(self.url)
        if not m:
            return None

        return int(m.group(1))

    def parse_numero(self):
        m = self.RE_SCRUTIN_URL.search(self.url)
        if not m:
            return None

        return int(m.group(2))

    def parse_date(self):
        if not self.soup.title:
            return None

        m = self.RE_DATE.search(self.soup.title.text)
        return extract_datetime(m.group(1)) if m else None

    def parse_groupes(self):
        return [
            ScrutinGroupe.build(self.url, tt)
            for tt in self.soup.select('.TTgroupe')
        ]


class ScrutinSyntheseParser(object):
    def __init__(self, url, html):
        self.url = url
        self.html = html

        self.soup = BeautifulSoup(html, 'html5lib')

    def parse(self):
        return ScrutinSynthese(
            votants=self.parse_votants(),
            exprimes=self.parse_exprimes(),
            majorite_absolue=self.parse_majorite_absolue(),
            pour=self.parse_pour(),
            contre=self.parse_contre(),
            resultat=self.parse_resultat()
        )

    def get_number(self, soup):
        return int(soup.b.text) if soup.b else None

    def get_number_by_id(self, id):
        def match(node):
            return node.has_attr('id') and node['id'] == id

        return self.get_number(
            next(filter(match, self.soup.select('.repartitionvotes'))))

    def get_number_by_text(self, text):
        def match(node):
            return node.text.startswith(text)

        return self.get_number(
            next(filter(match, self.soup.select('.repartitionvotes'))))

    def parse_votants(self):
        return self.get_number_by_id('total')

    def parse_exprimes(self):
        return self.get_number_by_text('Nombre de suffrages exprimés')

    def parse_majorite_absolue(self):
        return self.get_number_by_text('Majorité absolue')

    def parse_pour(self):
        return self.get_number_by_id('pour')

    def parse_contre(self):
        return self.get_number_by_id('contre')

    def parse_resultat(self):
        node = self.soup.select('.annonce .annoncevote')[0]
        if not node:
            return None

        return (ScrutinSynthese.ADOPTE
                if ScrutinSynthese.ADOPTE in node.text
                else ScrutinSynthese.REJETE)


class ScrutinGroupeParser(object):
    RE_NOM = re.compile(r'(.*) \(\d+ membres?\)')
    RE_DEPUTE = re.compile(r'([^> ]+(?: d(?:e|u|es))?) <b>([^<]+)</b>')

    def __init__(self, url, soup):
        self.url = url
        self.soup = soup

    def parse(self):
        return ScrutinGroupe(
            groupe=self.parse_groupe(),
            pour=self.parse_pour(),
            contre=self.parse_contre(),
            abstention=self.parse_abstentions(),
            nonvotants=self.parse_nonvotants()
        )

    def parse_groupe(self):
        node = self.soup.select('p.nomgroupe')
        if not len(node):
            return None

        m = self.RE_NOM.match(node[0].text)
        return m.group(1) if m else None

    def parse_liste_deputes(self, selector):
        ul = self.soup.select(selector)

        if len(ul):
            # Parsing html direct car dans certains cas le <ul class="deputes">
            # ne contient que du texte, pas de <li>.
            html = str(ul[0]).replace('\xa0', ' ')
            return [
                '%s %s' % nom
                for nom in self.RE_DEPUTE.findall(html)
            ]

        return []

    def parse_pour(self):
        return self.parse_liste_deputes('.Pour ul.deputes')

    def parse_contre(self):
        return self.parse_liste_deputes('.Contre ul.deputes')

    def parse_abstentions(self):
        return self.parse_liste_deputes('.Abstention ul.deputes')

    def parse_nonvotants(self):
        return self.parse_liste_deputes('.Non-votants ul.deputes')
