# re-write of the dosleg parser to have
# the same output as senapy

import json
import sys
from urllib.parse import urljoin, parse_qs, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup


def _log_error(error):
    print('## ERROR ###', error, file=sys.stderr)


def clean_url(url):
    if 'legifrance.gouv.fr' in url:
        scheme, netloc, path, params, query, fragment = urlparse(url)
        url_jo_params = parse_qs(query)
        if 'cidTexte' in url_jo_params:
            query = 'cidTexte=' + url_jo_params['cidTexte'][0]
        res = urlunparse((scheme, netloc, path, '', query, fragment))
        res = res.replace('http://legifrance.gouv.fr', 'https://www.legifrance.gouv.fr')
        res = res.replace('/jo_pdf.do?id=', '/affichTexte.do?cidTexte=')
        return res.replace('/./affichTexte.do', '/affichTexte.do')
    # url like 'pjl09-518.htmlhttp://www.assemblee-nationale.fr/13/ta/ta0518.asp'
    if url.find('http://') > 0:
        url = 'http://' + url.split('http://')[1]
    # url like http://www.senat.fr/dossier-legislatif/www.conseil-constitutionnel.fr/decision/2012/2012646dc.htm
    if 'www.conseil-' in url:
        url = 'http://www.conseil-' + url.split('www.conseil-')[1]
        url = url.replace('//', '/')
    if 'senat.fr' in url:
        url = url.replace('/dossierleg/', '/dossier-legislatif/')
        url = url.replace('http://', 'https://')
    url = url.replace('http://webdim/', 'http://www.assemblee-nationale.fr/')
    return url.strip()


def parse(html, url_an=None, verbose=True, first_dosleg_in_page=True):
    data = {
        'url_dossier_assemblee': url_an,
        'urgence': False,
    }

    log_error = _log_error
    if not verbose:
        def log_error(x): return None

    soup = BeautifulSoup(html, 'lxml')

    data['steps'] = []
    last_parsed = None
    curr_institution = 'assemblee'
    curr_stage = None
    last_section = None  # Travaux des commissions/Discussion en séance publique
    travaux_prep_already = False
    promulgation_step = None
    another_dosleg_inside = None

    if first_dosleg_in_page:
        metas = {}
        for meta in soup.select('meta'):
            if 'name' in meta.attrs:
                metas[meta.attrs['name']] = meta.attrs['content']

        url_jo = metas.get('LIEN_LOI_PROMULGUEE')
        if url_jo:
            data['url_jo'] = clean_url(url_jo)
            promulgation_step = {
                'institution': 'gouvernement',
                'stage': 'promulgation',
                'source_url': data['url_jo'],
            }

    for i, line in enumerate(html.split('\n')):
        def parsed():
            nonlocal last_parsed
            last_parsed = BeautifulSoup(line, 'lxml')
            return last_parsed.text.strip()

        def get_last_step():
            if len(data['steps']) > 0:
                return data['steps'][-1]
            return {}

        if '<font face="ARIAL" size="3" color="#000080">' in line:
            data['long_title'] = parsed()
        if '<br><b><font color="#000099">Travaux des commissions</font></b><br>' in line:
            last_section = parsed()
        if '<p align="center"><b><font color="#000080">Travaux préparatoires</font></b><br>' in line:
            if travaux_prep_already:
                log_error('FOUND ANOTHER DOSLEG INSIDE THE DOSLEG')
                another_dosleg_inside = '\n'.join(html.split('\n')[i:])
                break
            travaux_prep_already = True

        # Senat 1ère lecture, CMP, ...
        if '<font color="#000099" size="2" face="Arial">' in line:
            text = parsed()
            last_section = None
            if 'Dossier en ligne sur le site du Sénat' in text:
                data['url_dossier_senat'] = clean_url(last_parsed.select(
                    'a')[-1].attrs['href']).replace('/dossierleg/', '/dossier-legislatif/')
                text = text.replace(
                    '(Dossier en ligne sur le site du Sénat)', '')
            if 'Sénat' in text:
                curr_institution = 'senat'
            elif 'Assemblée nationale' in text:
                curr_institution = 'assemblee'
            elif 'Commission Mixte Paritaire' in text or 'Lecture texte CMP' in text:
                curr_institution = 'CMP'
                curr_stage = 'CMP'
            elif 'Conseil Constitutionnel' in text:
                curr_institution = 'conseil constitutionnel'
                curr_stage = 'constitutionnalité'
            elif 'Congrès du Parlement' in text:
                curr_institution = 'congrès'
                curr_stage = 'congrès'

            if '1ère lecture' in text:
                curr_stage = '1ère lecture'
            elif '2e lecture' in text:
                curr_stage = '2ème lecture'
            elif 'Nouvelle lecture' in text:
                curr_stage = 'nouv. lect.'
            elif 'Lecture définitive' in text:
                curr_stage = 'l. définitive'
            if not curr_stage:
                curr_stage = text.split('-')[-1].strip().lower()

            if curr_stage == "création de la commission d'enquête":
                log_error('COMMISSION D\'ENQUETE')
                return None

        if '>Proposition de résolution européenne<' in line:
            log_error('PROPOSITION DE RESOLUTION EUROPEENE')
            return None

        curr_step = None
        # conseil. consti. has no step but we should get the link
        no_step_but_good_link = False
        if 'Rapport portant également sur les propositions' in line:
            continue
        elif '>Projet de loi' in line or '>Proposition de loi' in line or '>Proposition de résolution' in line:
            curr_step = 'depot'
            if curr_stage == 'CMP':
                continue
        elif ">Texte de la commission" in line or '/ta-commission/' in line:
            if get_last_step().get('step') == 'commission':
                log_error('DOUBLE COMMISSION LINE: %s' % line)
                # remove last step since we prefer text links instead of reports links
                # TODO: add report link as bonus_url
                last_url = get_last_step().get('source_url')
                if ('/rapports/' in last_url or '/rap/' in last_url):
                    data['steps'] = data['steps'][:-1]
                # looks like the last url was already a text, let's assume it's a multi-depot
                else:
                    # TODO: re-order multi depot
                    curr_step = 'depot'
                    pass
            curr_step = 'commission'
        elif '/ta/' in line or '/tas' in line:
            if get_last_step().get('stage') != curr_stage:
                curr_step = 'depot'
            else:
                curr_step = 'hemicycle'
        elif ('/rapports/' in line or '/rap/' in line) and last_section and 'commissions' in last_section:
            if get_last_step().get('step') == 'commission':
                log_error('DOUBLE COMMISSION LINE: %s' % line)
                continue
            curr_step = 'commission'
        elif 'www.conseil-constitutionnel.fr/decision/' in line:
            no_step_but_good_link = True

        if curr_step or no_step_but_good_link:
            text = parsed()
            links = [a.attrs.get('href') for a in last_parsed.select('a')]
            links = [
                href for href in links if href and 'fiches_id' not in href and '/senateur/' not in href and 'javascript:' not in href]
            if not links:
                log_error('NO LINK IN LINE: %s' % (line,))
                continue
            urls_raps = []
            urls_others = []
            for href in links:
                if '/rap/' in href or '/rapports/' in href:
                    urls_raps.append(href)
                else:
                    urls_others.append(href)

            if len(urls_others) > 0:
                url = urls_others[0]
            else:
                url = urls_raps[0]

            url = clean_url(urljoin(url_an, url))

            real_institution = curr_institution
            if curr_stage == 'CMP' and curr_step == 'hemicycle':
                if 'assemblee-nationale.fr' in url:
                    real_institution = 'assemblee'
                elif 'senat.fr' in url:
                    real_institution = 'senat'

            step = {
                'institution': real_institution,
                'stage': curr_stage,
                'source_url': url,
            }

            if curr_step:
                step['step'] = curr_step

            data['steps'].append(step)

        if 'publiée au Journal Officiel' in line:
            text = parsed()
            links = [a.attrs['href'] for a in last_parsed.select(
                'a') if 'legifrance' in a.attrs.get('href', '')]
            if not links:
                log_error('NO GOOD LINK IN LINE: %s' % (line,))
                continue
            url_jo = links[-1]
            if 'url_jo' not in data:
                data['url_jo'] = url_jo
            promulgation_step = {
                'institution': 'gouvernement',
                'stage': 'promulgation',
                'source_url': url_jo,
            }

        if 'Le Gouvernement a engagé la procédure accélérée' in line or 'engagement de la procédure accélérée' in line:
            data['urgence'] = True

    if promulgation_step:
        data['steps'].append(promulgation_step)

    if another_dosleg_inside:
        others = parse(another_dosleg_inside, url_an, verbose=verbose, first_dosleg_in_page=False)
        if others:
            return [data] + others
    return [data]


if __name__ == '__main__':
    url = sys.argv[1]
    if url.startswith('http'):
        html = requests.get(url).text
        data = parse(html, url)
    else:
        html = open(url).read()
        url = html.split('-- URL=')[-1].split('-->')[0].strip()
        data = parse(html, url)
    print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
