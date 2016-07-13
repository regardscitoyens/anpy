# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup


def parse_dossier_legislatif(url, html_response):
    data = {
        'url': url
    }

    soup = BeautifulSoup(html_response, "html5lib")
    data['title'] = soup.head.title.text.replace(u'Assemblée nationale - ', '')

    return data