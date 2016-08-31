# -*- coding: utf-8 -*-

import xmltodict

__all__ = ['parse_question']


def parse_question(url, xml):
    data = xmltodict.parse(xml)['QUESTION']
    data['URL'] = url
    return data
