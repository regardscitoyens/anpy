# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime

from anpy.utils.date_utils import extract_datetime


def test_extract_date():
    assert extract_datetime('15 mai 2013 à 14 heures 30') == datetime(2013, 5, 15, 14, 30)
    assert extract_datetime('lundi 17 juin 2013') == datetime(2013, 6, 17)
    assert extract_datetime('mercredi 11 septembre 2013') == datetime(2013, 9, 11)
    assert extract_datetime('24 mars 2015 à 17 heures') == datetime(2015, 3, 24, 17, 0)
