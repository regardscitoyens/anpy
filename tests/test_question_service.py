# -*- coding: utf-8 -*-

from anpy.service import QuestionSearchService


def test_get():
    service = QuestionSearchService()
    assert 5 == len(service.get(legislature=13, size=5).results)


def test_is_answer():
    service = QuestionSearchService()
    response = service.get(legislature=13, size=5, is_answered=1)
    assert response.results[0].answer_date is not None


def test_iter():
    iterator = QuestionSearchService().iter(legislature=13, size=5)
    next(iterator)
    second_page_result = next(iterator)
    assert 5 == len(second_page_result.results)
