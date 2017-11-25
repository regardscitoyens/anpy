import codecs

import attr
from bs4 import BeautifulSoup

from anpy.amendement import parse_amendements_summary, parse_amendement, remove_inline_css_and_invalid_tags


def test_remove_inline_css_and_invalid_tags():
    soup = BeautifulSoup('<p style="text-align: justify;">Test <b>bold</b>, and <i>italic<b> with bold </b><u>and with u</u></i></p><p> 2nd test <i>italic</i></p>', 'html5lib')
    assert remove_inline_css_and_invalid_tags(soup.body) == '<p>Test bold, and italic with bold and with u</p><p> 2nd test italic</p>'


def test_json_parsing():
    json_response = {
        'data_table': [
            'S-AMANR5L14PO59051B996N4|996|Justice : d\xe9ch\xe9ance de la nationalit\xe9 pour tout individu portant les armes contre l\'arm\xe9e et la police|http://www.assemblee-nationale.fr/14/dossiers/decheance_nationalite_contre_armees_police.asp|Lois|CL4|http://www.assemblee-nationale.fr/14/amendements/0996/CION_LOIS/CL4.asp|Article UNIQUE||21 novembre 2014|M. Coronado et M. Molac|Adopt\xe9',
            'S-AMANR5L14PO59051B996N1|996|Justice : d\xe9ch\xe9ance de la nationalit\xe9 pour tout individu portant les armes contre l\'arm\xe9e et la police|http://www.assemblee-nationale.fr/14/dossiers/decheance_nationalite_contre_armees_police.asp|Lois|CL1|http://www.assemblee-nationale.fr/14/amendements/0996/CION_LOIS/CL1.asp|Article UNIQUE||21 novembre 2014|M. Meunier, rapporteur|Tomb\xe9',
        ],
        'infoGenerales': {
            'debut': 1,
            'description_schema': 'id|numInit|titreDossierLegislatif|urlDossierLegislatif|instance|numAmend|urlAmend|designationArticle|designationAlinea|dateDepot|signataires|sort',
            'nb_docs': 2500,
            'nb_resultats': 6123,
            'schema': 'partiel'
        }
    }

    expected_result = {
        'id': 'S-AMANR5L14PO59051B996N4',
        'num_init': '996',
        'titre_dossier_legislatif': 'Justice : d\xe9ch\xe9ance de la nationalit\xe9 pour tout individu portant les armes contre l\'arm\xe9e et la police',
        'url_dossier_legislatif': 'http://www.assemblee-nationale.fr/14/dossiers/decheance_nationalite_contre_armees_police.asp',
        'instance': 'Lois',
        'num_amend': 'CL4',
        'url_amend': 'http://www.assemblee-nationale.fr/14/amendements/0996/CION_LOIS/CL4.asp',
        'designation_article': 'Article UNIQUE',
        'designation_alinea': '',
        'date_depot': '21 novembre 2014',
        'signataires': 'M. Coronado et M. Molac',
        'sort': 'Adopt\xe9',
        'legislature': '14',
        'mission_visee': None,
    }

    parsed_result = parse_amendements_summary('', json_response)

    assert parsed_result.url == ''
    assert parsed_result.start == 1
    assert parsed_result.size == 2500
    assert parsed_result.total_count == 6123
    assert expected_result == attr.asdict(parsed_result.results[0])


def test_html_parsing():
    html = codecs.open('tests/resources/amendements/14_amendements_0996_CION_LOIS_CL4.html', encoding='utf-8').read()
    parsing_result = parse_amendement('http://www.assemblee-nationale.fr/14/amendements/0996/CION_LOIS/CL4.asp', html)

    expected_result = {
        'amend_parent': '',
        'auteur_id': '610860',
        'auteurs': 'M. Coronado et M. Molac',
        'code': '',
        'cosignataires_id': '607619',
        'date_badage': '24/11/2014',
        'date_sort': '26/11/2014',
        'deliberation': '',
        'designation_alinea': '',
        'designation_article': 'ART. UNIQUE',
        'dispositif': '<p>Supprimer cet article.</p>',
        'etape': '1ère lecture (1ère assemblée saisie)',
        'expose': '<p>La pr\xe9sente proposition de loi souhaite permettre la d\xe9ch\xe9ance de nationalit\xe9 \xe0 toute personne portant les armes contre les forces arm\xe9es fran\xe7aises et de police, ou leurs alli\xe9s.</p><p>Actuellement la loi pr\xe9voit d\xe9j\xe0 la possible de d\xe9choir de leur nationalit\xe9 fran\xe7aise les personnes condamn\xe9e<span>s</span> pour un crime ou d\xe9lit constituant une atteinte aux int\xe9r\xeats fondamentaux de la nation et les personnes condamn\xe9es, en France ou \xe0 l\'\xe9tranger, pour crime \xe0 au moins cinq ann\xe9es d\'emprisonnement.</p><p>Au-del\xe0 de son affichage, la pr\xe9sente proposition de loi ne couvrirait pas de cas nouveaux. Elle vise surtout \xe0 supprimer des garanties essentielles.</p><p>Comme le propose le rapporteur, l\'avis du Conseil d\'Etat resterait syst\xe9matique, mais il ne serait plus obligatoirement suivi. C\'est pourtant une garantie fondamentale. La garantie temporelle pr\xe9vu \xe0 l\'article 25-1 du code civil serait \xe9galement abrog\xe9e.</p><p>Il est \xe0 noter que la proposition de loi vise les personnes ayant acquis la nationalit\xe9 fran\xe7aise. Il est pourtant dangereux de consid\xe9rer qu\'il y aurait plusieurs cat\xe9gories de citoyens.</p><p>Les r\xe9centes affaires montrent \xe9galement que le probl\xe8me de \xab\xa0djihaddistes fran\xe7ais\xa0\xbb n\'est pas un probl\xe8me de binationaux, ou de personnes qui auraient acquis la nationalit\xe9 fran\xe7aise.</p><p>Pour toutes ces raisons, il est propos\xe9 de supprimer l\'article unique de cette loi.</p>',
        'groupe_id': '656014',
        'legislature': '14',
        'mission': '',
        'num_amtxt': 'CL4',
        'num_amend': '4',
        'num_init': '996',
        'num_partie': '',
        'ordre_texte': 'eaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaac',
        'refcode': '',
        'seance': '',
        'sort': 'Adopté',
        'titre_init': 'DÉCHÉANCE DE NATIONALITÉ POUR LES ATTEINTES AUX FORCES ARMÉES ET DE POLICE(n°996)',
        'url_division': '/14/textes/0996.asp#D_Article_unique',
        'url_dossier': 'http://www.assemblee-nationale.fr/14/dossiers/decheance_nationalite_contre_armees_police.asp',
        'url': 'http://www.assemblee-nationale.fr/14/amendements/0996/CION_LOIS/CL4.asp',
    }

    assert expected_result == attr.asdict(parsing_result)


def test_if_comments_are_removed():
    html = codecs.open('tests/resources/amendements/14_amendements_0922_AN_406.html', encoding='utf-8').read()
    data = parse_amendement('http://www.assemblee-nationale.fr/14/amendements/0922/AN/406.asp', html)

    assert data.dispositif == '<p></p><p>Supprimer le mot :</p><p></p><p>« républicaine ».</p><p></p>'
