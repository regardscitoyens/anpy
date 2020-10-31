import json, sys

from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

URL_TEMPLATE_SEANCE = "http://videos.assemblee-nationale.fr/seance-publique.p{page}"
URL_TEMPLATE_COMMISSION = "http://videos.assemblee-nationale.fr/commissions.p{page}"


def _extract_from_template(url_template, type):
    page = 1
    urls = set()
    prev_len_urls = 0
    while True:
        print(type, "page", page, file=sys.stderr)
        url = url_template.format(page=page)
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, 'lxml')
        should_break = False
        for video_el in soup.select('#myCarousel-contenu .span4'):
            url = urljoin(url, video_el.select_one('.vl')['href'])
            print(json.dumps({
                'type': type,
                'url': url,
            }))
            if url in urls:
                should_break = True
                break
            urls.add(url)
        if should_break or len(urls) == prev_len_urls:
            break
        page += 1
        prev_len_urls = len(urls)


def parse_videos_list():
    _extract_from_template(URL_TEMPLATE_SEANCE, 'seance')
    _extract_from_template(URL_TEMPLATE_COMMISSION, 'commission')
