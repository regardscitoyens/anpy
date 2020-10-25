import json

from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

URL_TEMPLATE = "http://www2.assemblee-nationale.fr/scrutins/liste/(offset)/{offset}/(legislature)/15/(type)/TOUS/(idDossier)/TOUS"


def parse_tableau_scrutins():
    num = None
    nums = set()
    offset = 0
    while True:
        url = URL_TEMPLATE.format(offset=offset)
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text)
        should_break = False
        for line in soup.select('#listeScrutins tbody tr'):
            cells = list(line.select("td"))
            links = list(cells[2].select('a'))
            link_dos = None
            if len(links) == 2:
                link_dos = urljoin(url, links[0]["href"])
                link_scrutin = urljoin(url, links[1]["href"])
            else:
                link_scrutin = urljoin(url, links[0]["href"])
            num = int(cells[0].text.strip().replace('*', ''))
            if num in nums:
                should_break = True
                break
            nums.add(num)
            data = {
                "numero": num,
                "date": cells[1].text.strip(),
                "objet": cells[2].text.replace('[dossier] [analyse du scrutin]', '').strip(),
                "pour": int(cells[3].text.strip()),
                "contre": int(cells[4].text.strip()),
                "abstention": int(cells[5].text.strip()),
                "url_dossier": link_dos,
                "url_scrutin": link_scrutin,
            }
            print(json.dumps(data, ensure_ascii=False))
        if should_break:
            break
        offset += 100
