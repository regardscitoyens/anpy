# -*- coding: utf-8 -*-

import codecs

from anpy.question import parse_question


def test_question_parsing():
    xml = codecs.open('tests/resources/questions/q14_14-47351QE.xml').read()
    parsing_result = parse_question('http://questions.assemblee-nationale.fr/q14/14-47351QE.htm', xml)

    assert ['@TYPE', 'LEGISLATURE', 'DEPOT', 'AUTEUR', 'GROUPE', 'CIRCONSCRIPTION', 'INDEXATION_AN', 'MINI', 'MINA',
            'ERRATUM_QUESTION', 'SIGNALEMENT', 'RENOUVELLEMENT', 'CLOTURE', 'REPONSE', 'ERRATUM_REPONSE',
            'URL'] == list(parsing_result.keys())
