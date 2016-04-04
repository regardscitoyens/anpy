# -*- coding: utf-8 -*-

import xmltodict


def parse_question(response):
    return xmltodict.parse(response.content)['QUESTION']