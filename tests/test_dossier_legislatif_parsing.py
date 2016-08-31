# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import codecs
from datetime import datetime
from bs4 import BeautifulSoup

from anpy.model import DecisionStatus
from anpy.parsing.json_utils import json_dumps, json_loads
from anpy.parsing.dossier_legislatif_parser import (
    parse_dossier_legislatif,
    clean_html,
    filter_dossier_element,
    DossierNode,
    LegislativeStepNode,
    ProcedureAccelereeNode,
    ProcedureParlementaire,
    LegislativeAct,
    LegislativeStep,
    EtudeImpactNode,
    AvisConseilEtatNode,
    DiscussionSeancePubliqueNode,
    DepotLoiNode,
)


def test_html_clean():
    bad_html = '<div> first part <br><br> second part'
    expected_html = '<p>first part</p>\n<p>second part</p>\n'

    assert expected_html == clean_html(bad_html)


def test_relevant_parent():
    root = DossierNode()
    step_node = LegislativeStepNode(parent=root)
    root.add_child(step_node)
    act_node = DepotLoiNode(parent=step_node)
    step_node.add_child(act_node)

    assert root == act_node.get_relevant_parent(LegislativeStepNode)
    assert step_node == act_node.get_relevant_parent(EtudeImpactNode)
    assert step_node == act_node.get_relevant_parent(ProcedureAccelereeNode)
    assert step_node == step_node.get_relevant_parent(ProcedureAccelereeNode)


def test_get_depot_loi_node():
    root = DossierNode()
    step_node = LegislativeStepNode(parent=root)
    root.add_child(step_node)
    act_node = DepotLoiNode(parent=step_node)
    step_node.add_child(act_node)

    assert act_node == root.get_first_depot_loi_node()


def test_filtering_elemnts():
    element_to_ignore = BeautifulSoup('<p>_</p>', 'html5lib')
    element_to_ignore_2 = BeautifulSoup('<p><a href=""></a>  </p>', 'html5lib')
    element_to_ignore_3 = BeautifulSoup('<p><a href="/index.asp">Accueil</a> &gt; <a href="/14/documents/index-dossier.asp">Dossiers</a></p>', 'html5lib')

    assert not filter_dossier_element(element_to_ignore)
    assert not filter_dossier_element(element_to_ignore_2)
    assert not filter_dossier_element(element_to_ignore_3)


def test_etude_impact_matching():
    etude_impact = BeautifulSoup('<p><a href="/14/projets/pl2302-ei.asp" target="_blank">Etude d\'impact</a></p>')

    assert EtudeImpactNode.match(etude_impact)


def test_avis_ce_matching():
    avis_element = BeautifulSoup('<p><a href="/14/pdf/projets/pl3318-ace.pdf">Avis du Conseil d\'État</a></p>')

    assert AvisConseilEtatNode.match(avis_element)


def test_dicussion_seance_matching():
    dicussion_element = BeautifulSoup('<p>Discussion en séance publique</p>')

    assert DiscussionSeancePubliqueNode.match(dicussion_element)


def test_depot_loi_matching():
    depot_element_1 = BeautifulSoup(
        '<p><a href="/14/projets/pl3318.asp">Projet de loi</a> pour une République numérique, n° 3318, déposé le 9 décembre 2015 (mis en ligne le 9 décembre 2015 à 18 heures 50)</p>')

    depot_element_2 = BeautifulSoup(
        '<p><a href="/14/projets/pl3318.asp">Projet de loi</a> , adopté, par l\'Assemblée nationale après engagement de la procédure accélérée, relatif au renseignement, n° 424, déposé le 5 mai 2015.</p>')

    assert DepotLoiNode.match(depot_element_1)
    assert DepotLoiNode.match(depot_element_2)


def test_legislative_acts_matching():
    procedure_acceleree = BeautifulSoup('<p>Le Gouvernement a engagé la procédure accélérée sur ce projet.</p>')

    assert ProcedureAccelereeNode.match(procedure_acceleree)


def test_legislative_steps_matching():
    an_first_lecture = BeautifulSoup('<p><strong>Assemblée nationale - 1ère lecture</strong></p>')
    senat_first_lecture = BeautifulSoup('<p><strong>Sénat - 1ère lecture</strong></p>')
    cmp = BeautifulSoup('<p><strong>Commission Mixte Paritaire (Désaccord)</strong></p>')
    an_new_lecture = BeautifulSoup('<p><strong>Assemblée nationale - Nouvelle lecture</strong></p>')
    senat_new_lecture = BeautifulSoup('<p><strong>Sénat - Nouvelle lecture</strong></p>')
    an_final_lecture = BeautifulSoup('<p><strong>Assemblée nationale - Lecture définitive</strong></p>')
    cc = BeautifulSoup('<p><strong>Conseil Constitutionnel</strong></p>')

    assert LegislativeStepNode.match(an_first_lecture)
    assert LegislativeStepNode.match(senat_first_lecture)
    assert LegislativeStepNode.match(cmp)
    assert LegislativeStepNode.match(an_new_lecture)
    assert LegislativeStepNode.match(senat_new_lecture)
    assert LegislativeStepNode.match(an_final_lecture)
    assert LegislativeStepNode.match(cc)


def test_etude_impact_data_extractor():
    etude_element = BeautifulSoup('<p><a href="/14/projets/pl2302-ei.asp" target="_blank">Etude d\'impact</a></p>')
    act = EtudeImpactNode()
    act.add_element(etude_element)
    act_data = act.extract_data()

    assert act_data['type'] == LegislativeAct.ETUDE_IMPACT
    assert act_data['url'] == 'http://www.assemblee-nationale.fr/14/projets/pl2302-ei.asp'


def test_avis_ce_data_extractor():
    avis_element = BeautifulSoup('<p><a href="/14/pdf/projets/pl3318-ace.pdf" target="_blank">Avis du Conseil d\'État</a></p>')
    act = AvisConseilEtatNode()
    act.add_element(avis_element)
    act_data = act.extract_data()

    assert act_data['type'] == LegislativeAct.AVIS_CONSEIL_ETAT
    assert act_data['url'] == 'http://www.assemblee-nationale.fr/14/pdf/projets/pl3318-ace.pdf'


def test_discussion_seance_extractor():
    discussion_element_1 = BeautifulSoup('<p>Discussion en séance publique</p>', 'html5lib')
    discussion_element_2 = BeautifulSoup('<p><strong><a href="/14/cri/2014-2015/20150212.asp">1<sup>ère</sup> séance du'
                                         ' lundi 13 avril 2015</a></strong></p>', 'html5lib')
    scrutin_element = BeautifulSoup('<p><a href="/14/scrutins/jo1109.asp">Scrutin public</a> n° 1109 sur l\'ensemble du'
                                    ' projet de loi relatif au renseignement (première lecture) au cours de la 2e '
                                    'séance du mardi 5 mai 2015</p>', 'html5lib')
    decision_element = BeautifulSoup('<p>Projet de loi relatif au renseignement, adopté en 1ère lecture par '
                                     'l\'Assemblée nationale le 5 mai 2015 , <a href="/14/ta/ta0511.asp"> TA n° '
                                     '511 </a></p>', 'html5lib')

    act = DiscussionSeancePubliqueNode()
    act.add_element(discussion_element_1)
    act.add_element(discussion_element_2)
    act.add_element(scrutin_element)
    act.add_element(decision_element)

    act_data = act.extract_data()

    assert act_data['type'] == LegislativeAct.DISCUSSION_SEANCE_PUBLIQUE
    assert act_data['seances'] == [{
        'url': 'http://www.assemblee-nationale.fr/14/cri/2014-2015/20150212.asp',
        'date': datetime(2015, 4, 13)
    }]
    assert act_data['decision'] == {
        'date': datetime(2015, 5, 5),
        'url': 'http://www.assemblee-nationale.fr/14/ta/ta0511.asp',
        'status': DecisionStatus.ADOPTED
    }


def test_depot_loi_extractor():
    depot_element = BeautifulSoup(
        '<p><a href="/14/projets/pl3318.asp">Projet de loi</a> pour une République numérique, n° 3318, déposé le 9 décembre 2015 (mis en ligne le 9 décembre 2015 à 18 heures 50)</p>', 'html5lib')
    act = DepotLoiNode()
    act.add_element(depot_element)
    act_data = act.extract_data()

    assert act_data['type'] == LegislativeAct.DEPOT_INITIATIVE
    assert act_data['url'] == 'http://www.assemblee-nationale.fr/14/projets/pl3318.asp'
    assert act_data['date'] == datetime(2015, 12, 9)


def test_legislative_step_data_extractor():
    an_first_lecture = BeautifulSoup('<p><strong>Assemblée nationale - 1ère lecture</strong></p>')
    step = LegislativeStepNode()
    step.add_element(an_first_lecture)

    etude_impact = BeautifulSoup('<p><a href="/14/projets/pl2302-ei.asp" target="_blank">Etude d\'impact</a></p>')
    act = EtudeImpactNode(parent=step)
    act.add_element(etude_impact)

    step.add_child(act)

    step_data = step.extract_data()

    assert step_data['type'] == LegislativeStep.AN_PREMIERE_LECTURE
    assert step_data['acts'] == [{
        'type': LegislativeAct.ETUDE_IMPACT,
        'url': 'http://www.assemblee-nationale.fr/14/projets/pl2302-ei.asp'
    }]


def test_dossier_data_extractor():
    pjl_element = BeautifulSoup('<p><a href="/14/projets/pl3318.asp">Projet de loi</a> pour une République numérique, n° 3318, déposé le 9 décembre 2015 (mis en ligne le 9 décembre 2015 à 18 heures 50)</p>')
    depot = DepotLoiNode()
    depot.add_element(pjl_element)

    an_first_lecture_element = BeautifulSoup('<p><strong>Assemblée nationale - 1ère lecture</strong></p>')
    step = LegislativeStepNode()
    step.add_element(an_first_lecture_element)
    step.add_child(depot)

    dossier = DossierNode()
    title_element = BeautifulSoup('<p><strong>Questions sociales et santé : modernisation de notre système de santé</strong></p>')
    dossier.add_element(title_element)

    dossier.add_child(step)

    dossier_data = dossier.extract_data()

    assert dossier_data['title'] == 'Questions sociales et santé : modernisation de notre système de santé'
    assert dossier_data['steps'] == [{
        'type': LegislativeStep.AN_PREMIERE_LECTURE,
        'acts': [{
            'type': LegislativeAct.DEPOT_INITIATIVE,
            'url': 'http://www.assemblee-nationale.fr/14/projets/pl3318.asp',
            'date': datetime(2015, 12, 9)
        }]
    }]
    assert dossier_data['legislature'] == '14'
    assert dossier_data['procedure'] == ProcedureParlementaire.PJL


def test_pjl_sante_parsing():
    url = 'http://www.assemblee-nationale.fr/14/dossiers/sante.asp'
    html = codecs.open('tests/resources/14_dossiers_sante.html', encoding='iso-8859-1').read()
    dossier_data = parse_dossier_legislatif(url, html)
    dossier_data = json_loads(json_dumps(dossier_data))
    expected_data = json_loads(
        codecs.open('tests/resources/14_dossiers_sante.json', encoding='utf-8').read())
    assert dossier_data == expected_data


def test_pjl_num_parsing():
    url = 'http://www.assemblee-nationale.fr/14/dossiers/republique_numerique.asp'
    html = codecs.open('tests/resources/14_dossiers_republique_numerique.html', encoding='iso-8859-1').read()
    dossier_data = parse_dossier_legislatif(url, html)
    dossier_data = json_loads(json_dumps(dossier_data))
    expected_data = json_loads(
        codecs.open('tests/resources/14_dossiers_republique_numerique.json', encoding='utf-8').read())
    assert dossier_data == expected_data




