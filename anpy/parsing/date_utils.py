# -*- coding: utf-8 -*-

import dateparser
import re

hours_with_minutes_re = re.compile(' heures ')
hours_without_minutes = re.compile(' heures$')


def extract_datetime(text):
    text = hours_with_minutes_re.sub(':', text.strip())
    text = hours_without_minutes.sub(':00', text)

    return dateparser.parse(text, languages=['fr'])
