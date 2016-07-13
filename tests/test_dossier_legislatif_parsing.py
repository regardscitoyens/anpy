# -*- coding: utf-8 -*-

import requests
from anpy.parsing.dossier_legislatif_parser import parse_dossier_legislatif


def test_pjl_num_parsing():
    parsing_result = parse_dossier_legislatif(
        "http://www.assemblee-nationale.fr/14/dossiers/republique_numerique.asp",
        requests.get("http://www.assemblee-nationale.fr/14/dossiers/republique_numerique.asp").content
    )

    assert u"Economie : pour une République numérique" == parsing_result["title"]
    assert u"http://www.assemblee-nationale.fr/14/dossiers/republique_numerique.asp" == parsing_result["url"]