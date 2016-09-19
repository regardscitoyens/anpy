# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import codecs
from bs4 import BeautifulSoup

from anpy.scrutin import (
    ScrutinGroupeParser,
    ScrutinParser,
    ScrutinSynthese,
    ScrutinSyntheseParser
)
from anpy.utils import json_dumps, json_loads



def test_parse_title():
    html = """
    <h3 class="president-title">Scrutin public sur l'ensemble du projet de loi pour une République numérique (première lecture).</h3>
    <h3></h3>
    """

    parser = ScrutinParser('', html)
    assert parser.parse_title() == 'Scrutin public sur l\'ensemble du projet de loi pour une République numérique (première lecture).'


def test_parse_legislature():
    url = 'http://www2.assemblee-nationale.fr/scrutins/detail/(legislature)/14/(num)/1212'

    parser = ScrutinParser(url, '')
    assert parser.parse_legislature() == 14


def test_parse_numero():
    url = 'http://www2.assemblee-nationale.fr/scrutins/detail/(legislature)/14/(num)/1212'

    parser = ScrutinParser(url, '')
    assert parser.parse_numero() == 1212


def test_parse_date():
    html = """
    <title>Analyse du scrutin n° 1212 - Première séance du 26/01/2016 - Assemblée nationale</title>
    """

    parser = ScrutinParser('', html)
    assert parser.parse_date().strftime('%Y-%m-%d') == '2016-01-26'


SYNTHESE_HTML = """
<p id="total" class="repartitionvotes total">Nombre de votants : <b>544</b></p>
<p class="repartitionvotes">Nombre de suffrages exprimés : <b>357</b></p>
<p class="repartitionvotes">Majorité absolue : <b>179</b></p>
<p id="pour" class="repartitionvotes votes">Pour l'adoption : <b>356</b></p>
<p id="contre" class="repartitionvotes votes">Contre : <b>1</b></p>
<p class="annonce"><span class="annoncevote">L'Assemblée nationale a adopté.</span></p>
"""


def test_synthese_parse_votants():
    parser = ScrutinSyntheseParser('', SYNTHESE_HTML)
    assert parser.parse_votants() == 544


def test_synthese_parse_exprimes():
    parser = ScrutinSyntheseParser('', SYNTHESE_HTML)
    assert parser.parse_exprimes() == 357


def test_synthese_parse_majorite_absolue():
    parser = ScrutinSyntheseParser('', SYNTHESE_HTML)
    assert parser.parse_majorite_absolue() == 179


def test_synthese_parse_pour():
    parser = ScrutinSyntheseParser('', SYNTHESE_HTML)
    assert parser.parse_pour() == 356


def test_synthese_parse_contre():
    parser = ScrutinSyntheseParser('', SYNTHESE_HTML)
    assert parser.parse_contre() == 1


def test_synthese_parse_resultat():
    parser = ScrutinSyntheseParser('', SYNTHESE_HTML)
    assert parser.parse_resultat() == ScrutinSynthese.ADOPTE


TTGROUPE_SOUP = BeautifulSoup("""
<div class="TTgroupe">
    <a class="agroupe" name="Groupe socialiste, républicain et citoyen" id="G0"></a>
    <p class="nomgroupe">Groupe socialiste, républicain et citoyen (287 membres)</p>
    <div class="Pour">
        <p class="typevote">Pour: <b>272</b></p>
        <ul class="deputes">
            <li>            Ibrahim&nbsp;<b>Aboubacar</b></li><li> Patricia&nbsp;<b>Adam</b></li><li> Sylviane&nbsp;<b>Alaux</b></li><li> Jean-Pierre&nbsp;<b>Allossery</b></li><li> Pouria&nbsp;<b>Amirshahi</b></li><li> François&nbsp;<b>André</b></li><li>Nathalie&nbsp;<b>Appéré</b></li>
        </ul>
    </div>
    <div class="Contre">
        <p class="typevote">Contre: <b>1</b></p>
        <ul class="deputes">
            <li>            Nicolas&nbsp;<b>Dhuicq</b></li><li> François de&nbsp;<b>Rugy</b></li>
        </ul>
    </div>
    <div class="Abstention">
    <p class="typevote">Abstention: <b>184</b></p>
    <ul class="deputes">
    <li>            Bernard&nbsp;<b>Accoyer</b></li><li> Yves&nbsp;<b>Albarello</b></li><li> Nicole&nbsp;<b>Ameline</b></li><li> Benoist&nbsp;<b>Apparu</b></li><li> Laurence&nbsp;<b>Arribagé</b></li><li> Julien&nbsp;<b>Aubert</b></li><li>Olivier&nbsp;<b>Audibert-Troin</b></li>
    </ul>
    </div>
    <div class="Non-votants">
        <p class="typevote">Non-votants: <b>2</b></p>
        <ul class="deputes">
        MM.&nbsp;Claude&nbsp;<b>Bartolone</b>&nbsp;(Président&nbsp;de&nbsp;l'Assemblée&nbsp;nationale) et David&nbsp;<b>Habib</b>&nbsp;(Président&nbsp;de&nbsp;séance).
        </ul>
    </div>
</div>
""", 'html5lib')


def test_groupe_parse_nom():
    parser = ScrutinGroupeParser('', TTGROUPE_SOUP)
    assert parser.parse_groupe() == 'Groupe socialiste, républicain et citoyen'


def test_groupe_parse_pour():
    parser = ScrutinGroupeParser('', TTGROUPE_SOUP)
    assert parser.parse_pour() == [
        "Ibrahim Aboubacar",
        "Patricia Adam",
        "Sylviane Alaux",
        "Jean-Pierre Allossery",
        "Pouria Amirshahi",
        "François André",
        "Nathalie Appéré"
    ]


def test_groupe_parse_contre():
    parser = ScrutinGroupeParser('', TTGROUPE_SOUP)
    assert parser.parse_contre() == [
        "Nicolas Dhuicq",
        "François de Rugy"
    ]


def test_groupe_parse_abstentions():
    parser = ScrutinGroupeParser('', TTGROUPE_SOUP)
    assert parser.parse_abstentions() == [
        "Bernard Accoyer",
        "Yves Albarello",
        "Nicole Ameline",
        "Benoist Apparu",
        "Laurence Arribagé",
        "Julien Aubert",
        "Olivier Audibert-Troin"
    ]


def test_groupe_parse_nonvotants():
    parser = ScrutinGroupeParser('', TTGROUPE_SOUP)
    assert parser.parse_nonvotants() == [
        "Claude Bartolone",
        "David Habib"
    ]


def test_pjl_num_parsing():
    url = 'http://www2.assemblee-nationale.fr/scrutins/detail/(legislature)/14/(num)/1212'
    html_path = 'tests/resources/scrutins/14_num_1212.html'
    json_path = 'tests/resources/scrutins/14_num_1212.json'

    html = codecs.open(html_path, encoding='utf-8').read()
    scrutin = json_loads(json_dumps(ScrutinParser(url, html).parse().to_dict()))
    expected = json_loads(codecs.open(json_path, encoding='utf-8').read())

    assert scrutin == expected
