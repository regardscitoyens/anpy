import codecs
from datetime import datetime

from bs4 import BeautifulSoup

from anpy.dossier import (
    ProcedureParlementaire,
    LegislativeStepType,
    LegislativeActType,
    EtudeImpactNode,
    DossierParser,
    clean_html,
    filter_dossier_element,
    DossierNode,
    LegislativeStepNode,
    ProcedureAccelereeNode,
    DepotLoiNode,
    DecisionNode,
    DiscussionSeancePubliqueNode,
    AvisConseilEtatNode,
    DecisionStatus)
from anpy.utils import json_dumps, json_loads

from anpy.dossier_like_senapy import parse as parse_like_senapy


def test_html_clean():
    bad_html = '<div> first part <br><br> second part'
    expected_html = '<p>first part</p>\n<p>second part</p>\n'

    assert expected_html == clean_html(bad_html)


def test_parse_legislature():
    html = """
    <p><a href=""></a></p>'
    <p><a href="/index.asp">Accueil</a> &gt; <a href="/14/documents/index-dossier.asp">Dossiers</a></p>
    """

    parser = DossierParser('', html)

    assert parser.parse_legislature() == '14'


def test_parse_title():
    html = """
    <html><head></head><body><p><a href="/index.asp">Accueil</a> &gt; <a href="/14/documents/index-dossier.asp">Dossiers</a></p>
    <hr/>
    <h2><a href="/juniors/schema.asp"><img alt="" src="/images/procedure.jpg"/></a>  </h2>
    <p><strong>Economie : pour une République numérique</strong></p>
    """

    parser = DossierParser('', html)

    assert parser.parse_title() == 'Economie : pour une République numérique'


def test_parse_procedure():
    html = """
    <html><head></head><body><p><a href="/index.asp">Accueil</a> &gt; <a href="/14/documents/index-dossier.asp">Dossiers</a></p>
    <p><strong>Assemblée nationale - 1ère lecture</strong></p>
    <p><a href="/14/projets/pl3318.asp">Projet de loi</a> pour une République numérique, n° 3318, déposé le 9 décembre 2015 (mis en ligne le 9 décembre 2015 à 18 heures 50)</p>
    <p>et renvoyé à <a href="/commissions/59051_tab.asp">la commission des lois constitutionnelles, de la législation et de l'administration générale de la république</a></p>

    """

    parser = DossierParser('', html)

    assert parser.parse_procedure() == ProcedureParlementaire.PJL


def test_parse_senat_url():
    html = """
    <p><a href="/14/scrutins/jo1212.asp">Scrutin public</a> n° 1212 sur l'ensemble du projet de loi pour une République numérique (première lecture) au cours de la 1ère séance du mardi 26 janvier 2016</p>
    <p>Projet de loi pour une République numérique, adopté en 1ère lecture par l'Assemblée nationale le 26 janvier 2016 , <a href="/14/ta/ta0663.asp"> TA n° 663 </a></p>
    <p><strong>Sénat - 1ère lecture</strong></p>
    <p><a href="http://www.senat.fr/dossier-legislatif/pjl15-325.html"><em>(Dossier en ligne sur le site du Sénat)</em></a></p>
    """

    parser = DossierParser('', html)

    assert parser.parse_senat_url() == 'http://www.senat.fr/dossier-legislatif/pjl15-325.html'


def test_parse_senat_url_alt():
    html = """
    <p align="center"><b><font color="#000080">Travaux préparatoires</font></b><br>
    <div align="center"><a href="#ETAPE257051"> <font face="Arial" size="1">Sénat 1<sup>ère</sup> lecture</font></a> - <a href="#ETAPE257052"> <font face="Arial" size="1">Assemblée nationale 1<sup>ère</sup> lecture</font></a> - <a href="#ETAPE257054"> <font face="Arial" size="1">Commission Mixte Paritaire</font></a> - <a href="#ETAPE257055"> <font face="Arial" size="1">Lecture texte CMP</font></a></div><p>
    <p align="center"><b><font color="#000099" size="2" face="Arial"><a name="ETAPE257051"></a>Sénat - 1<sup>ère</sup> lecture</b><br><a target="_blank" href="http://www.senat.fr/dossierleg/pjl08-582.html"><i>(Dossier en ligne sur le site du Sénat)</i></a></font></b></p>

    <p><div align="left"><a target="_blank" href="http://www.senat.fr/leg/pjl08-582.html">Projet de loi</a> relatif à l'action extérieure de l'État, n° 582 rectifié, déposé le  22 juillet 2009<br> et renvoyé à la commission des affaires étrangères, de la défense et des forces armées<br>
    """

    parser = DossierParser('', html)

    assert parser.parse_senat_url() == 'http://www.senat.fr/dossierleg/pjl08-582.html'


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


def test_filtering_elements():
    element_to_ignore = BeautifulSoup('<p>_</p>', 'html5lib')
    element_to_ignore_2 = BeautifulSoup('<p><a href=""></a>  </p>', 'html5lib')
    element_to_ignore_3 = BeautifulSoup('<p><a href="/index.asp">Accueil</a> &gt; <a href="/14/documents/index-dossier.asp">Dossiers</a></p>', 'html5lib')

    assert not filter_dossier_element(element_to_ignore)
    assert not filter_dossier_element(element_to_ignore_2)
    assert not filter_dossier_element(element_to_ignore_3)


def test_etude_impact_matching():
    etude_impact = BeautifulSoup('<p><a href="/14/projets/pl2302-ei.asp" target="_blank">Etude d\'impact</a></p>', 'html5lib')

    assert EtudeImpactNode.match(etude_impact)


def test_avis_ce_matching():
    avis_element = BeautifulSoup('<p><a href="/14/pdf/projets/pl3318-ace.pdf">Avis du Conseil d\'État</a></p>', 'html5lib')

    assert AvisConseilEtatNode.match(avis_element)


def test_dicussion_seance_matching():
    dicussion_element = BeautifulSoup('<p>Discussion en séance publique</p>', 'html5lib')

    assert DiscussionSeancePubliqueNode.match(dicussion_element)


def test_depot_loi_matching():
    depot_element_1 = BeautifulSoup(
        '<p><a href="/14/projets/pl3318.asp">Projet de loi</a> pour une République numérique, n° 3318, déposé le 9 décembre 2015 (mis en ligne le 9 décembre 2015 à 18 heures 50)</p>', 'html5lib')

    depot_element_2 = BeautifulSoup(
        '<p><a href="/14/projets/pl3318.asp">Projet de loi</a> , adopté, par l\'Assemblée nationale après engagement de la procédure accélérée, relatif au renseignement, n° 424, déposé le 5 mai 2015.</p>', 'html5lib')

    assert DepotLoiNode.match(depot_element_1)
    assert DepotLoiNode.match(depot_element_2)


def test_decision_node_matching():
    depot_element = BeautifulSoup(
        '<p><a href="/14/projets/pl3318.asp">Projet de loi</a> pour une République numérique, n° 3318, déposé le 9 décembre 2015 (mis en ligne le 9 décembre 2015 à 18 heures 50)</p>', 'html5lib')

    decision_element = BeautifulSoup(
        '<p>Projet de loi pour une République numérique, adopté en 1ère lecture par l\'Assemblée nationale le 26 janvier 2016 , <a href="/14/ta/ta0663.asp"> TA n° 663 </a></p>', 'html5lib')

    assert not DecisionNode.match(depot_element)
    assert DecisionNode.match(decision_element)


def test_legislative_acts_matching():
    procedure_acceleree = BeautifulSoup('<p>Le Gouvernement a engagé la procédure accélérée sur ce projet.</p>', 'html5lib')

    assert ProcedureAccelereeNode.match(procedure_acceleree)


def test_legislative_steps_matching():
    an_first_lecture = BeautifulSoup('<p><strong>Assemblée nationale - 1ère lecture</strong></p>', 'html5lib')
    senat_first_lecture = BeautifulSoup('<p><strong>Sénat - 1ère lecture</strong></p>', 'html5lib')
    cmp = BeautifulSoup('<p><strong>Commission Mixte Paritaire (Désaccord)</strong></p>', 'html5lib')
    an_new_lecture = BeautifulSoup('<p><strong>Assemblée nationale - Nouvelle lecture</strong></p>', 'html5lib')
    senat_new_lecture = BeautifulSoup('<p><strong>Sénat - Nouvelle lecture</strong></p>', 'html5lib')
    an_final_lecture = BeautifulSoup('<p><strong>Assemblée nationale - Lecture définitive</strong></p>', 'html5lib')
    cc = BeautifulSoup('<p><strong>Conseil Constitutionnel</strong></p>', 'html5lib')

    assert LegislativeStepNode.match(an_first_lecture)
    assert LegislativeStepNode.match(senat_first_lecture)
    assert LegislativeStepNode.match(cmp)
    assert LegislativeStepNode.match(an_new_lecture)
    assert LegislativeStepNode.match(senat_new_lecture)
    assert LegislativeStepNode.match(an_final_lecture)
    assert LegislativeStepNode.match(cc)


def test_etude_impact_data_extractor():
    etude_element = BeautifulSoup('<p><a href="/14/projets/pl2302-ei.asp" target="_blank">Etude d\'impact</a></p>', 'html5lib')
    act = EtudeImpactNode()
    act.add_element(etude_element)
    act_data = act.extract_data()[0]

    assert act_data['type'] == LegislativeActType.ETUDE_IMPACT
    assert act_data['url'] == 'http://www.assemblee-nationale.fr/14/projets/pl2302-ei.asp'


def test_avis_ce_data_extractor():
    avis_element = BeautifulSoup('<p><a href="/14/pdf/projets/pl3318-ace.pdf" target="_blank">Avis du Conseil d\'État</a></p>', 'html5lib')
    act = AvisConseilEtatNode()
    act.add_element(avis_element)
    act_data = act.extract_data()[0]

    assert act_data['type'] == LegislativeActType.AVIS_CONSEIL_ETAT
    assert act_data['url'] == 'http://www.assemblee-nationale.fr/14/pdf/projets/pl3318-ace.pdf'


def test_discussion_seance_extractor():
    discussion_element_1 = BeautifulSoup('<p>Discussion en séance publique</p>', 'html5lib')
    discussion_element_2 = BeautifulSoup('<p><strong><a href="/14/cri/2014-2015/20150212.asp">1<sup>ère</sup> séance du'
                                         ' lundi 13 avril 2015</a></strong></p>', 'html5lib')
    scrutin_element = BeautifulSoup('<p><a href="/14/scrutins/jo1109.asp">Scrutin public</a> n° 1109 sur l\'ensemble du'
                                    ' projet de loi relatif au renseignement (première lecture) au cours de la 2e '
                                    'séance du mardi 5 mai 2015</p>', 'html5lib')

    act = DiscussionSeancePubliqueNode()
    act.add_element(discussion_element_1)
    act.add_element(discussion_element_2)

    act_data = act.extract_data()[0]

    assert act_data['type'] == LegislativeActType.DISCUSSION_SEANCE_PUBLIQUE
    assert act_data['url'] == 'http://www.assemblee-nationale.fr/14/cri/2014-2015/20150212.asp'
    assert act_data['date'] == datetime(2015, 4, 13)


def test_depot_loi_extractor():
    depot_element = BeautifulSoup(
        '<p><a href="/14/projets/pl3318.asp">Projet de loi</a> pour une République numérique, n° 3318, déposé le 9 décembre 2015 (mis en ligne le 9 décembre 2015 à 18 heures 50)</p>', 'html5lib')
    act = DepotLoiNode()
    act.add_element(depot_element)
    act_data = act.extract_data()[0]

    assert act_data['type'] == LegislativeActType.DEPOT_INITIATIVE
    assert act_data['url'] == 'http://www.assemblee-nationale.fr/14/projets/pl3318.asp'
    assert act_data['date'] == datetime(2015, 12, 9)


def test_decision_node_extractor():
    decision_element = BeautifulSoup(
        '<p>Projet de loi pour une République numérique, adopté en 1<sup>ère</sup> lecture par l\'Assemblée nationale le 26 janvier 2016, <a href="/14/ta/ta0663.asp"> TA n° 663 </a></p>', 'html5lib')

    act = DecisionNode()
    act.add_element(decision_element)
    act_data = act.extract_data()[0]

    assert act_data['status'] == DecisionStatus.ADOPTE
    assert act_data['url'] == 'http://www.assemblee-nationale.fr/14/ta/ta0663.asp'
    assert act_data['date'] == datetime(2016, 1, 26)


def test_legislative_step_data_extractor():
    an_first_lecture = BeautifulSoup('<p><strong>Assemblée nationale - 1ère lecture</strong></p>', 'html5lib')
    step = LegislativeStepNode()
    step.add_element(an_first_lecture)

    etude_impact = BeautifulSoup('<p><a href="/14/projets/pl2302-ei.asp" target="_blank">Etude d\'impact</a></p>', 'html5lib')
    act = EtudeImpactNode(parent=step)
    act.add_element(etude_impact)

    step.add_child(act)

    step_data = step.extract_data()

    assert step_data['type'] == LegislativeStepType.AN_PREMIERE_LECTURE
    assert step_data['acts'] == [{
        'type': LegislativeActType.ETUDE_IMPACT,
        'url': 'http://www.assemblee-nationale.fr/14/projets/pl2302-ei.asp'
    }]


def test_legislative_step_2eme_lecture():
    an_first_lecture = BeautifulSoup('<p align="center"><b><font color="#000099" size="2" face="Arial"><a name="ETAPE269073"></a>Assemblée nationale - 2<sup>e</sup> lecture</font></b></p>', 'html5lib')
    step = LegislativeStepNode()
    step.add_element(an_first_lecture)
    step_data = step.extract_data()

    assert step_data['type'] == LegislativeStepType.AN_DEUXIEME_LECTURE

def test_dossier_data_extractor():
    pjl_element = BeautifulSoup('<p><a href="/14/projets/pl3318.asp">Projet de loi</a> pour une République numérique, n° 3318, déposé le 9 décembre 2015 (mis en ligne le 9 décembre 2015 à 18 heures 50)</p>', 'html5lib')
    depot = DepotLoiNode()
    depot.add_element(pjl_element)

    an_first_lecture_element = BeautifulSoup('<p><strong>Assemblée nationale - 1ère lecture</strong></p>', 'html5lib')
    step = LegislativeStepNode()
    step.add_element(an_first_lecture_element)
    step.add_child(depot)

    dossier = DossierNode()
    title_element = BeautifulSoup('<p><strong>Questions sociales et santé : modernisation de notre système de santé</strong></p>', 'html5lib')
    dossier.add_element(title_element)

    dossier.add_child(step)

    steps = dossier.extract_data()

    assert steps == [{
        'type': LegislativeStepType.AN_PREMIERE_LECTURE,
        'acts': [{
            'type': LegislativeActType.DEPOT_INITIATIVE,
            'url': 'http://www.assemblee-nationale.fr/14/projets/pl3318.asp',
            'date': datetime(2015, 12, 9)
        }]
    }]


def test_pjl_sante_parsing():
    url = 'http://www.assemblee-nationale.fr/14/dossiers/sante.asp'
    html = codecs.open('tests/resources/dossiers/14_dossiers_sante.html', encoding='iso-8859-1').read()
    dossier = DossierParser(url, html).parse()
    dossier_data = json_loads(json_dumps(dossier.to_dict()))
    expected_data = json_loads(
        codecs.open('tests/resources/dossiers/14_dossiers_sante.json', encoding='utf-8').read())
    assert dossier_data == expected_data

    dossier_data = parse_like_senapy(html, url)
    expected_data = json_loads(
        codecs.open('tests/resources/dossiers/14_dossiers_sante.senapy.json', encoding='utf-8').read())
    assert dossier_data == expected_data


def test_pjl_num_parsing():
    url = 'http://www.assemblee-nationale.fr/14/dossiers/republique_numerique.asp'
    html = codecs.open('tests/resources/dossiers/14_dossiers_republique_numerique.html', encoding='iso-8859-1').read()
    dossier = DossierParser(url, html).parse()
    dossier_data = json_loads(json_dumps(dossier.to_dict()))
    expected_data = json_loads(
        codecs.open('tests/resources/dossiers/14_dossiers_republique_numerique.json', encoding='utf-8').read())
    assert dossier_data == expected_data

    dossier_data = parse_like_senapy(html, url)
    expected_data = json_loads(
        codecs.open('tests/resources/dossiers/14_dossiers_republique_numerique.senapy.json', encoding='utf-8').read())
    assert dossier_data == expected_data


