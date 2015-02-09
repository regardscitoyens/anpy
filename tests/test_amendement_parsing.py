# -*- coding: utf-8 -*-

import unittest

import requests
from bs4 import BeautifulSoup

from anpy.parsing.amendement_parser import parse_amendements_summary, parse_amendement, remove_inline_css_and_invalid_tags


class AmendementParsingTest(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_remove_inline_css_and_invalid_tags(self):
        soup = BeautifulSoup('<p style="text-align: justify;">Test <b>bold</b>, and <i>italic<b> with bold </b><u>and with u</u></i></p><p> 2nd test <i>italic</i></p>')
        self.assertEqual(remove_inline_css_and_invalid_tags(soup), '<p>Test bold, and italic with bold and with u</p><p> 2nd test italic</p>')

    def test_json_parsing(self):
        json_response = {
            u'data_table': [
                u"S-AMANR5L14PO59051B996N4|996|Justice : d\xe9ch\xe9ance de la nationalit\xe9 pour tout individu portant les armes contre l'arm\xe9e et la police|http://www.assemblee-nationale.fr/14/dossiers/decheance_nationalite_contre_armees_police.asp|Lois|CL4|http://www.assemblee-nationale.fr/14/amendements/0996/CION_LOIS/CL4.asp|Article UNIQUE||21 novembre 2014|M. Coronado et M. Molac|Adopt\xe9",
                u"S-AMANR5L14PO59051B996N1|996|Justice : d\xe9ch\xe9ance de la nationalit\xe9 pour tout individu portant les armes contre l'arm\xe9e et la police|http://www.assemblee-nationale.fr/14/dossiers/decheance_nationalite_contre_armees_police.asp|Lois|CL1|http://www.assemblee-nationale.fr/14/amendements/0996/CION_LOIS/CL1.asp|Article UNIQUE||21 novembre 2014|M. Meunier, rapporteur|Tomb\xe9",
            ],
            u'infoGenerales': {
                u'debut': 1,
                u'description_schema': u'id|numInit|titreDossierLegislatif|urlDossierLegislatif|instance|numAmend|urlAmend|designationArticle|designationAlinea|dateDepot|signataires|sort',
                u'nb_docs': 2500,
                u'nb_resultats': 6123,
                u'schema': u'partiel'
            }
        }

        expected_result = {
            u'id': u'S-AMANR5L14PO59051B996N4',
            u'num_init': u'996',
            u'titre_dossier_legislatif': u"Justice : d\xe9ch\xe9ance de la nationalit\xe9 pour tout individu portant les armes contre l'arm\xe9e et la police",
            u'url_dossier_legislatif': u'http://www.assemblee-nationale.fr/14/dossiers/decheance_nationalite_contre_armees_police.asp',
            u'instance': u'Lois',
            u'num_amend': u'CL4',
            u'url_amend': u'http://www.assemblee-nationale.fr/14/amendements/0996/CION_LOIS/CL4.asp',
            u'designation_article': u'Article UNIQUE',
            u'designation_alinea': u'',
            u'date_depot': u'21 novembre 2014',
            u'signataires': u'M. Coronado et M. Molac',
            u'sort': u'Adopt\xe9',
            u'legislature': u'14',
        }

        parsed_result = parse_amendements_summary('', json_response)

        self.assertEqual(parsed_result.url, '')
        self.assertEqual(parsed_result.start, 1)
        self.assertEqual(parsed_result.size, 2500)
        self.assertEqual(parsed_result.total_count, 6123)
        self.assertDictEqual(expected_result, parsed_result.results[0].__dict__)

    def test_html_parsing(self):
        parsing_result = parse_amendement(
            "http://www.assemblee-nationale.fr/14/amendements/0996/CION_LOIS/CL4.asp",
            requests.get("http://www.assemblee-nationale.fr/14/amendements/0996/CION_LOIS/CL4.asp").content
        )

        expected_result = {
            u'amend_parent': u'',
            u'auteur_id': u'610860',
            u'auteurs': u'M. Coronado et M. Molac',
            u'code': u'',
            u'cosignataires_id': u'607619',
            u'date_badage': u'24/11/2014',
            u'date_sort': u'26/11/2014',
            u'deliberation': u'',
            u'designation_alinea': u'',
            u'designation_article': u'ART. UNIQUE',
            u'dispositif': u'<p>Supprimer cet article.</p>',
            u'etape': u'1ère lecture (1ère assemblée saisie)',
            u'expose': u'<p>La pr\xe9sente proposition de loi souhaite permettre la d\xe9ch\xe9ance de nationalit\xe9 \xe0 toute personne portant les armes contre les forces arm\xe9es fran\xe7aises et de police, ou leurs alli\xe9s.</p><p>Actuellement la loi pr\xe9voit d\xe9j\xe0 la possible de d\xe9choir de leur nationalit\xe9 fran\xe7aise les personnes condamn\xe9e<span>s</span> pour un crime ou d\xe9lit constituant une atteinte aux int\xe9r\xeats fondamentaux de la nation et les personnes condamn\xe9es, en France ou \xe0 l\'\xe9tranger, pour crime \xe0 au moins cinq ann\xe9es d\'emprisonnement.</p><p>Au-del\xe0 de son affichage, la pr\xe9sente proposition de loi ne couvrirait pas de cas nouveaux. Elle vise surtout \xe0 supprimer des garanties essentielles.</p><p>Comme le propose le rapporteur, l\'avis du Conseil d\'Etat resterait syst\xe9matique, mais il ne serait plus obligatoirement suivi. C\'est pourtant une garantie fondamentale. La garantie temporelle pr\xe9vu \xe0 l\'article 25-1 du code civil serait \xe9galement abrog\xe9e.</p><p>Il est \xe0 noter que la proposition de loi vise les personnes ayant acquis la nationalit\xe9 fran\xe7aise. Il est pourtant dangereux de consid\xe9rer qu\'il y aurait plusieurs cat\xe9gories de citoyens.</p><p>Les r\xe9centes affaires montrent \xe9galement que le probl\xe8me de \xab\xa0djihaddistes fran\xe7ais\xa0\xbb n\'est pas un probl\xe8me de binationaux, ou de personnes qui auraient acquis la nationalit\xe9 fran\xe7aise.</p><p>Pour toutes ces raisons, il est propos\xe9 de supprimer l\'article unique de cette loi.</p>',
            u'groupe_id': u'656014',
            u'legislature': u'14',
            u'mission': u'',
            u'num_amtxt': u'CL4',
            u'num_amend': u'4',
            u'num_init': u'996',
            u'num_partie': u'',
            u'ordre_texte': u'eaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaac',
            u'refcode': u'',
            u'seance': u'',
            u'sort': u'Adopté',
            u'titre_init': u'DÉCHÉANCE DE NATIONALITÉ POUR LES ATTEINTES AUX FORCES ARMÉES ET DE POLICE(n°996)',
            u'url_division': u'/14/textes/0996.asp#D_Article_unique',
            u'url_dossier': u'http://www.assemblee-nationale.fr/14/dossiers/decheance_nationalite_contre_armees_police.asp',
            u'url': u'http://www.assemblee-nationale.fr/14/amendements/0996/CION_LOIS/CL4.asp',
        }

        self.assertDictEqual(expected_result, parsing_result.__dict__)

if __name__ == '__main__':
    unittest.main()