# -*- coding: utf-8 -*-

import unittest

from anpy.service import AmendementSearchService


class AmendementSearchServiceTest(unittest.TestCase):
    def setUp(self):
        self.service = AmendementSearchService()

    def test_get(self):
        self.assertEqual(2, len(self.service.get(idDossierLegislatif=31515, idExamen=3295, rows=2).results))

    def test_total_count(self):
        self.assertEqual(5, self.service.total_count(idDossierLegislatif=31515, idExamen=3295))

    def test_iterator(self):
        iterator = self.service.iterator(idDossierLegislatif=31515, idExamen=3295, rows=2)
        next(iterator)
        next(iterator)
        last_page_result = next(iterator)
        self.assertEqual(1, len(last_page_result.results))

    def test_get_order(self):
        order = self.service.get_order(idDossierLegislatif=31515, idExamen=3295, rows=2)
        self.assertEqual(order, ['CD4', 'CD13', 'CD1', 'CD3', 'CD2'])
