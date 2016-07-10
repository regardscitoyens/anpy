# -*- coding: utf-8 -*-

import requests

from anpy.parsing.question_parser import parse_question


def test_question_parsing():
    response = requests.get('http://questions.assemblee-nationale.fr/q14/14-47351QE.htm/vue/xml')
    parsing_result = parse_question(response)

    assert ['@TYPE', 'LEGISLATURE', 'DEPOT', 'AUTEUR', 'GROUPE', 'CIRCONSCRIPTION', 'INDEXATION_AN', 'MINI', 'MINA',
            'ERRATUM_QUESTION', 'SIGNALEMENT', 'RENOUVELLEMENT', 'CLOTURE', 'REPONSE', 'ERRATUM_REPONSE'] \
           == list(parsing_result.keys())