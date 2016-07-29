# -*- coding: utf-8 -*-

import xmltodict

__all__ = ['parse_question']


def parse_question(response):
    return xmltodict.parse(response.content)['QUESTION']
