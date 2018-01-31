# re-write of the dosleg parser to have
# the same output as senapy

import json
import sys
import re
from urllib.parse import urljoin

import requests
import dateparser
from bs4 import BeautifulSoup

from lawfactory_utils.urls import clean_url


def format_date(date):
    parsed = dateparser.parse(date, languages=['fr'])
    return parsed.strftime("%Y-%m-%d")


def _log_error(error):
    print('## ERROR ###', error, file=sys.stderr)


def parse(html, url_an=None, verbose=True, first_dosleg_in_page=True):
    data = {
        'url_dossier_assemblee': clean_url(url_an),
        'urgence': False,
    }

    log_error = _log_error
    if not verbose:
        def log_error(x): return None

    soup = BeautifulSoup(html, 'lxml')

    data['assemblee_id'] = data['url_dossier_assemblee'].split('/')[-1].replace('.asp', '')
    legislature = data['url_dossier_assemblee'].split('.fr/')[1].split('/')[0]
    try:
        data['assemblee_legislature'] = int(legislature)
    except ValueError:  # strange link (old dosleg)
        log_error('NO LEGISLATURE IN AN LINK: ' + data['url_dossier_assemblee'])

    data['steps'] = []
    last_parsed = None
    curr_institution = 'assemblee'
    curr_stage = '1ère lecture'
    last_section = None  # Travaux des commissions/Discussion en séance publique
    travaux_prep_already = False
    promulgation_step = None
    another_dosleg_inside = None
    predicted_next_step = None # For unfinished projects, we try to catch the next step

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

    html_lines = html.split('\n')
    for i, line in enumerate(html_lines):
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

        if '>Accès aux Travaux préparatoires' in line:
            parsed()
            data['previous_works'] = clean_url(urljoin(url_an, last_parsed.find('a').attrs['href']))

        if '<div align="center"><font color="#000099"><b>En savoir plus</b>' in line:
            # end of dosleg
            break

        curr_step = None
        # conseil. consti. has no step but we should get the link
        no_step_but_good_link = False
        if 'Rapport portant également sur les propositions' in line:
            continue
        elif '>projet de loi' in line.lower() or '>Proposition de loi' in line or '>Proposition de résolution' in line:
            curr_step = 'depot'
            if curr_stage == 'CMP':
                continue
        elif ">Texte de la commission" in line or '/ta-commission/' in line:
            curr_step = 'commission'

            # no commission for l. définitive
            if curr_stage == 'l. définitive' and curr_step == 'commission':
                curr_step = 'hemicycle'

        elif '/ta/' in line or '/leg/tas' in line:
            if get_last_step().get('stage') != curr_stage:
                curr_step = 'depot'
                if curr_stage == 'CMP':
                    curr_step = 'commission'
            else:
                curr_step = 'hemicycle'
        elif ('/rapports/' in line or '/rap/' in line) and last_section and 'commissions' in last_section:
            if get_last_step().get('step') == 'commission':
                log_error('DOUBLE COMMISSION LINE: %s' % line)
                continue
            curr_step = 'commission'

            # no commission for l. définitive
            if curr_stage == 'l. définitive' and curr_step == 'commission':
                curr_step = 'hemicycle'
        elif 'www.conseil-constitutionnel.fr/decision/' in line:
            no_step_but_good_link = True

        if curr_step or no_step_but_good_link:
            # if same step previously, replace or not the url
            if get_last_step().get('step') == curr_step:
                log_error('DOUBLE STEP: %s' % line)
                # remove last step since we prefer text links instead of reports links
                # TODO: add report link as bonus_url
                last_url = get_last_step().get('source_url')
                if not last_url or ('/rapports/' in last_url or '/rap/' in last_url):
                    data['steps'] = data['steps'][:-1]
                # looks like the last url was already a text, let's assume it's a multi-depot
                else:
                    # multi-depot if not CMP
                    # TODO: re-order multi depot
                    if curr_institution == 'senat' and curr_stage != 'CMP':
                        curr_step = 'depot'

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

            cmp_commission_other_url = None
            if len(urls_others) > 0:
                url = urls_others[0]
                # CMP commission should produce two texts, one for each institution
                if curr_step == 'commission' and curr_stage == 'CMP':
                    cmp_commission_other_url = clean_url(urljoin(url_an, urls_others[1]))
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

            if cmp_commission_other_url:
                step['cmp_commission_other_url'] = cmp_commission_other_url

            # try to detect a date
            for test_line in (line, html_lines[i-1]):
                test_line = test_line.replace('1<sup>er</sup>', '1')
                date_match = re.search(r'(déposée? le|adoptée? .*? le|modifiée? .*?)\s*(\d\d? \w\w\w+ \d\d\d\d)', test_line, re.I)
                if date_match:
                    step['date'] = format_date(date_match.group(2))
                else:
                    date_match = re.search(r'(mis en ligne le)\s*(\d\d? \w\w\w+ \d\d\d\d)', test_line, re.I)
                    if date_match:
                        step['date'] = format_date(date_match.group(2))
            data['steps'].append(step)
            predicted_next_step = None

        if 'publiée au Journal Officiel' in line:
            text = parsed()
            links = [clean_url(a.attrs['href']) for a in last_parsed.select(
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

        # Next step prediction via small clues
        # TODO: this could be done via last_section (we parse two times the same thing)
        if '>Discussion en séance publique<' in line:
            predicted_next_step = {
                'institution': curr_institution,
                'stage': curr_stage,
                'step': 'hemicycle',
            }
        elif '>Travaux des commissions<' in line:
            # TODO: this fails for CMP hemicycle senat
            predicted_next_step = {
                'institution': curr_institution,
                'stage': curr_stage,
                'step': 'commission',
            }

    if promulgation_step:
        data['steps'].append(promulgation_step)

    # add predicted next step for unfinished projects
    if 'url_jo' not in data and not promulgation_step and predicted_next_step:
        data['steps'].append(predicted_next_step)

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


"""
Cas non-gérés:
- renvois en commision: http://www.assemblee-nationale.fr/14/dossiers/interdiction_prescription_acquisitive_voies_rurales.asp
- senat ppl manquant: http://www.assemblee-nationale.fr/13/dossiers/comite_poids_mesures.asp
- windows-1252 encoding: http://www.assemblee-nationale.fr/15/dossiers/responsabilite_financiere_dirigeants_benevoles_associations.asp
"""
