# -*- coding: utf-8 -*-
from builtins import str
import json
from datetime import datetime

import dateparser
import re

hours_with_minutes_re = re.compile(' heures ')
hours_without_minutes = re.compile(' heures$')


def extract_datetime(text):
    text = hours_with_minutes_re.sub(':', text.strip())
    text = hours_without_minutes.sub(':00', text)

    return dateparser.parse(text, languages=['fr'])


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


class JSONDecoder(json.JSONDecoder):
    DATETIME_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

    def __init__(self, *args, **kwargs):
        super(JSONDecoder, self).__init__(
            object_pairs_hook=self.object_pairs_hook,
            *args,
            **kwargs)

    def object_pairs_hook(self, obj):
        return dict((k, self.decode_on_match(v)) for k, v in obj)

    def decode_on_match(self, obj):
        string = str(obj)

        match = re.search(self.DATETIME_PATTERN, string)
        if match:
            return datetime.strptime(match.string, '%Y-%m-%dT%H:%M:%S')

        return obj


def json_dumps(data, *args, **kwargs):
    return JSONEncoder(*args, **kwargs).encode(data)


def json_loads(string, *args, **kwargs):
    return JSONDecoder(*args, **kwargs).decode(string)


def convert_camelcase_to_underscore(name):
    # thx to http://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-camel-case  # noqa
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
