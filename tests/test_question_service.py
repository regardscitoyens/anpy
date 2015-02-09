# -*- coding: utf-8 -*-

import unittest

from anpy.service import QuestionSearchService


class SearchQuestionServiceTest(unittest.TestCase):
    def test_get(self):
        service = QuestionSearchService()
        self.assertEqual(5, len(service.get(legislature=13, size=5).results))

    def test_is_answer(self):
        service = QuestionSearchService()
        response = service.get(legislature=13, size=5, is_answered=1)
        self.assertIsNotNone(response.results[0].answer_date)

    def test_iter(self):
        iterator = QuestionSearchService().iter(legislature=13, size=5)
        next(iterator)
        second_page_result = next(iterator)
        self.assertEqual(5, len(second_page_result.results))
