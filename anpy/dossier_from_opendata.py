"""
Experiment to use the JSON formatted data provided by the AN for the doslegs

  python dossier_from_opendata.py <dosleg_url>
"""

import sys
import json
import zipfile
import io
import re

from lawfactory_utils.urls import download, enable_requests_cache, clean_url, parse_national_assembly_url


def same_stage_step_instit(a, b):
    return a.get('stage') == b.get('stage') and a.get('step') == b.get('step') \
        and a.get('institution') == b.get('institution')


def yield_leafs(etape, path=None):
    if path is None:
        path = []
    if etape.get("actesLegislatifs"):
        for children in to_arr(etape["actesLegislatifs"]["acteLegislatif"]):
            yield from yield_leafs(children, path=path + [etape])
    else:
        yield path, etape


# TODO : make this generic for the latest legislature, for instance by finding the url of the zip in http://data.assemblee-nationale.fr/reunions/reunions
def find_texts_discussed_after(min_date, senate_urls=False, include_resolutions=False):
    OPEN_DATA_REUNIONS_URL = "http://data.assemblee-nationale.fr/static/openData/repository/15/vp/reunions/Agenda_XV.json.zip"
    reunions = download_open_data_file("Agenda_XV.json", OPEN_DATA_REUNIONS_URL)

    doslegs = set()
    for reunion in to_arr(reunions['reunions']['reunion']):

        date = reunion['timeStampDebut'].split('T')[0]
        if date < min_date:
            continue

        if not reunion.get('ODJ') or not reunion['ODJ'].get('pointsODJ'):
            continue

        for pointODJ in to_arr(reunion['ODJ']['pointsODJ']['pointODJ']):
            if not pointODJ['dossiersLegislatifsRefs']:
                continue
            for dosleg in to_arr(pointODJ['dossiersLegislatifsRefs']['dossierRef']):
                doslegs.add(dosleg)

    dossiers_json = download_open_data_doslegs(15)
    docs = {doc['dossierParlementaire']["uid"]: doc['dossierParlementaire'] for doc in dossiers_json["export"]["dossiersLegislatifs"]["dossier"]}

    doslegs_urls = set()
    for dosleg_ref in doslegs:
        if dosleg_ref not in docs:
            # TODO: dossierAbsorbantRef
            print('[anpy]', dosleg_ref, ' dosleg in ODJ but not found in Open Data', file=sys.stderr)
            continue
        dossier = docs[dosleg_ref]

        if dossier["@xsi:type"] != "DossierLegislatif_Type":
            continue

        if not include_resolutions and dossier["procedureParlementaire"]["libelle"] == "Résolution":
            continue

        titreChemin = dossier["titreDossier"]["titreChemin"]
        url_pattern = "http://www.assemblee-nationale.fr/dyn/{}/dossiers/{}"
        url = url_pattern.format(dossier["legislature"], titreChemin)
        url_senat = dossier["titreDossier"]["senatChemin"]
        if url_senat and senate_urls:
            url = clean_url(url_senat)
        doslegs_urls.add(url)

    return doslegs_urls


def to_arr(obj):
    if type(obj) is list:
        return obj
    return [obj]


def test_status(url):
    try:
        resp = download(url)
        if resp.status_code != 200:
            return False
    except Exception:
        return False
    return resp


def download_open_data_file(filename, file_url):
    raw_data = download(file_url)
    data_zip = zipfile.ZipFile(io.BytesIO(raw_data.content))
    if filename:
        with data_zip.open(filename) as d:
            return json.loads(d.read().decode('utf-8'))
    data = {
        "export": {
            "@xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "dossiersLegislatifs": {
                "dossier": []
            },
            "textesLegislatifs": {
                "document": []
            }
        }
    }
    for filename in data_zip.namelist():
        with data_zip.open(filename) as d:
            filedata = json.loads(d.read().decode('utf-8'))
            if "dossierParlementaire" in filename:
                data["export"]["dossiersLegislatifs"]["dossier"].append(filedata)
            else:
                data["export"]["textesLegislatifs"]["document"].append(filedata["document"])
    return data


def download_open_data_doslegs(legislature):
    files = {
        15: (
            None,
            "http://data.assemblee-nationale.fr/static/openData/repository/15/loi/dossiers_legislatifs/Dossiers_Legislatifs_XV.json.zip",
        ),
        14: (
            "Dossiers_Legislatifs_XIV.json",
            "http://data.assemblee-nationale.fr/static/openData/repository/14/loi/dossiers_legislatifs/Dossiers_Legislatifs_XIV.json.zip",
        ),
    }
    filename, file_url = files[legislature]
    return download_open_data_file(filename, file_url)


def an_text_url(identifiant, code):
    """
    Port of the PHP function used by the National Assembly:

    public function urlOpaque($identifiant, $codeType = NULL)
    {
        $datas = array(
            'PRJL' => array('repertoire' => 'projets', 'prefixe' => 'pl', 'suffixe' => ''),
            'PION' => array('repertoire' => 'propositions', 'prefixe' => 'pion', 'suffixe' => ''),
            'PNRECOMENQ' => array('repertoire' => 'propositions', 'prefixe' => 'pion', 'suffixe' => ''),
            'PNREAPPART341' => array('repertoire' => 'propositions', 'prefixe' => 'pion', 'suffixe' => ''),
            'PNREMODREGLTAN' => array('repertoire' => 'propositions', 'prefixe' => 'pion', 'suffixe' => ''),
            'AVCE' => array('repertoire' => 'projets', 'prefixe' => 'pl', 'suffixe' => '-ace'),
            'ETDI' => array('repertoire' => 'projets', 'prefixe' => 'pl', 'suffixe' => '-ei'),
            'ACIN' => array('repertoire' => 'projets', 'prefixe' => 'pl', 'suffixe' => '-ai'),
            'LETT' => array('repertoire' => 'projets', 'prefixe' => 'pl', 'suffixe' => '-l'),
            'PNRETVXINSTITEUROP' => array('repertoire' => 'europe/resolutions', 'prefixe' => 'ppe', 'suffixe' => ''),
            'PNRE' => array('repertoire' => 'europe/resolutions', 'prefixe' => 'ppe', 'suffixe' => ''),
            'RION' => array('repertoire' => '', 'prefixe' => '', 'suffixe' => ''),
            'TCOM' => array('repertoire' => 'ta-commission', 'prefixe' => 'r', 'suffixe' => '-a0'),
            'TCOMMODREGLTAN' => array('repertoire' => 'ta-commission', 'prefixe' => 'r', 'suffixe' => '-a0'),
            'TCOMTVXINSTITEUROP' => array('repertoire' => 'ta-commission', 'prefixe' => 'r', 'suffixe' => '-a0'),
            'TCOMCOMENQ' => array('repertoire' => 'ta-commission', 'prefixe' => 'r', 'suffixe' => '-a0'),
            'TADO' => array('repertoire' => 'ta', 'prefixe' => 'ta', 'suffixe' => ''),
        );
        preg_match('/(.{4})([ANS]*)(R[0-9])([LS]*)([0-9]*)([BTACP]*)(.*)/', $identifiant, $matches);
        $leg = $matches[5];
        $typeTa = $matches[6];
        $num = $matches[7];
        switch ($typeTa) {
            case 'BTC':
                $type = 'TCOM';
                break;
            case 'BTA':
                $type = 'TADO';
                break;
            default:
                $type = $codeType;
        }
        $host = "http://www.assemblee-nationale.fr/";
        return $host . $leg . "/" . $datas[$type]['repertoire'] . "/" . $datas[$type]['prefixe'] . $num . $datas[$type]['suffixe'] . ".pdf";
    }
    """
    datas = {
        'PRJL': {
            'repertoire': 'projets',
            'prefixe': 'pl',
            'suffixe': '',
        },
        'PION': {
            'repertoire': 'propositions',
            'prefixe': 'pion',
            'suffixe': '',
        },
        'PNRECOMENQ': {
            'repertoire': 'propositions',
            'prefixe': 'pion',
            'suffixe': '',
        },
        'PNREAPPART341': {
            'repertoire': 'propositions',
            'prefixe': 'pion',
            'suffixe': '',
        },
        'PNREMODREGLTAN': {
            'repertoire': 'propositions',
            'prefixe': 'pion',
            'suffixe': '',
        },
        'AVCE': {
            'repertoire': 'projets',
            'prefixe': 'pl',
            'suffixe': '-ace',
        },
        'ETDI': {
            'repertoire': 'projets',
            'prefixe': 'pl',
            'suffixe': '-ei',
        },
        'ACIN': {
            'repertoire': 'projets',
            'prefixe': 'pl',
            'suffixe': '-ai',
        },
        'LETT': {
            'repertoire': 'projets',
            'prefixe': 'pl',
            'suffixe': '-l',
        },
        'PNRETVXINSTITEUROP': {
            'repertoire': 'europe/resolutions',
            'prefixe': 'ppe',
            'suffixe': '',
        },
        'PNRE': {
            'repertoire': 'propositions',
            'prefixe': 'pion',
            'suffixe': '',
        },
        'RION': {
            'repertoire': '',
            'prefixe': '',
            'suffixe': '',
        },
        'TCOM': {
            'repertoire': 'ta-commission',
            'prefixe': 'r',
            'suffixe': '-a0',
        },
        'TCOMMODREGLTAN': {
            'repertoire': 'ta-commission',
            'prefixe': 'r',
            'suffixe': '-a0',
        },
        'TCOMTVXINSTITEUROP': {
            'repertoire': 'ta-commission',
            'prefixe': 'r',
            'suffixe': '-a0',
        },
        'TCOMCOMENQ': {
            'repertoire': 'ta-commission',
            'prefixe': 'r',
            'suffixe': '-a0',
        },
        'TADO': {
            'repertoire': 'ta',
            'prefixe': 'ta',
            'suffixe': '',
        },
        # NOT IN NATIONAL ASSEMBLY PHP CODE
        'RAPP': {
            'repertoire': 'rapports',
            'prefixe': 'r',
            'suffixe': '',
        },
        'RINF': {
            'repertoire': 'rapports',
            'prefixe': 'r',
            'suffixe': '',
        }
    }
    match = re.match(r'(.{4})([ANS]*)(R[0-9])([LS]*)([0-9]*)([BTACP]*)(.*)', identifiant)
    leg = match.group(5)
    typeTa = match.group(6)
    num = match.group(7)
    if typeTa == 'BTC':
        type = 'TCOM'
    elif typeTa == 'BTA':
        type = 'TADO'
    else:
        type = code
    host = "http://www.assemblee-nationale.fr/"

    if type not in datas:
        # ex: ALCNANR5L15B0002 (allocution du président)
        raise Exception('Unknown document type for %s' % identifiant)

    return host + leg + "/" + datas[type]['repertoire'] + "/" + datas[type]['prefixe'] + num + datas[type]['suffixe'] + ".asp"


def parse(url, logfile=sys.stderr, cached_opendata_an={}):
    def _log(*args):
        nonlocal logfile
        print(*args, file=logfile)

    legislature, _ = parse_national_assembly_url(url)
    if legislature and legislature in cached_opendata_an:
        dossiers_json = cached_opendata_an[legislature]
    else:
        dossiers_json = download_open_data_doslegs(legislature)

    docs = {doc["uid"]: doc for doc in dossiers_json["export"]["textesLegislatifs"]["document"]}

    for dossier in dossiers_json["export"]["dossiersLegislatifs"]["dossier"]:
        dossier = dossier["dossierParlementaire"]

        if dossier["@xsi:type"] != "DossierLegislatif_Type":
            continue

        titreChemin = dossier["titreDossier"]["titreChemin"]

        # find the right dosleg even if it's an old url
        url_common_part = "{}/dossiers/{}".format(dossier["legislature"], titreChemin)
        if not url.endswith(url_common_part):
            continue
        url = "http://www.assemblee-nationale.fr/dyn/{}".format(url_common_part)

        data = {}
        data["urgence"] = False
        url_senat = dossier["titreDossier"]["senatChemin"]
        if url_senat:
            data["url_dossier_senat"] = clean_url(url_senat)
        data["long_title"] = dossier["titreDossier"]["titre"]
        data["url_dossier_assemblee"] = clean_url(url)
        data["assemblee_legislature"] = int(dossier["legislature"])
        data["assemblee_slug"] = dossier["titreDossier"]["titreChemin"]
        data["assemblee_id"] = "%s-%s" % (dossier["legislature"], data["assemblee_slug"])

        if dossier["procedureParlementaire"]["libelle"] in (
            "Projet de loi de finances de l'année",
            "Projet de loi de financement de la sécurité sociale",
            "Projet de loi de finances rectificative",
            "Projet ou proposition de loi constitutionnelle",
        ):
            data['use_old_procedure'] = True

        data["steps"] = []
        step = None
        start_step = None
        for etape in to_arr(dossier["actesLegislatifs"]["acteLegislatif"]):
            for path, sous_etape in yield_leafs(etape):
                if sous_etape["@xsi:type"] in ("EtudeImpact_Type", "DepotAvisConseilEtat_Type"):
                    continue

                step = {}

                date = sous_etape.get("dateActe")
                if date:
                    step["date"] = date.split("T")[0]

                if sous_etape["@xsi:type"] == "ProcedureAccelere_Type":
                    data["urgence"] = True
                elif sous_etape["@xsi:type"] == "Promulgation_Type":
                    url = clean_url(sous_etape.get("urlLegifrance") or sous_etape["infoJO"]["urlLegifrance"])
                    data["url_jo"] = url
                    data["end"] = step["date"]

                    step["institution"] = "gouvernement"
                    step["stage"] = "promulgation"
                    step["source_url"] = url
                    data["steps"].append(step)
                    continue
                elif sous_etape["@xsi:type"] == "ConclusionEtapeCC_Type":
                    step["institution"] = "conseil constitutionnel"
                    step["stage"] = "constitutionnalité"
                    step["source_url"] = clean_url(sous_etape["urlConclusion"])
                    data["steps"].append(step)

                if "textesAssocies" in sous_etape:
                    # TODO review
                    sous_etape["texteAssocie"] = to_arr(sous_etape["textesAssocies"]["texteAssocie"])[0]["refTexteAssocie"]

                code = sous_etape.get("codeActe")

                if "AVIS-RAPPORT" in code or code == 'CMP-DEPOT':
                    continue

                if code.startswith("AN"):
                    step["institution"] = "assemblee"
                elif code.startswith("SN"):
                    step["institution"] = "senat"

                if "-DEPOT" in code:
                    step["step"] = "depot"
                elif "-COM" in code:
                    step["step"] = "commission"
                elif "-DEBATS" in code:
                    step["step"] = "hemicycle"

                if "1-" in code:
                    step["stage"] = "1ère lecture"
                elif "2-" in code:
                    step["stage"] = "2ème lecture"
                elif "3-" in code:
                    step["stage"] = "3ème lecture"  # TODO: else libelleCourt
                elif "NLEC-" in code:
                    step["stage"] = "nouv. lect."
                elif "ANLDEF-" in code:
                    step["stage"] = "l. définitive"
                    if step["step"] == "commission":
                        continue
                elif "CMP-" in code:
                    step["stage"] = "CMP"
                    if "-AN" in code:
                        step["institution"] = "CMP"
                    elif "-SN" in code:
                        step["institution"] = "senat"
                        if "RAPPORT-SN" in code:
                            # ignore the cmp_commission_other_url for now
                            continue
                    else:
                        step["institution"] = "CMP"
                elif "ANLUNI-" in code:
                    step["stage"] = "l. unique"

                step["id_opendata"] = sous_etape["uid"]

                # keep first step for a step-type (ex: first hemiycle)
                if start_step is None or not same_stage_step_instit(start_step, step):
                    start_step = step

                if "texteAdopte" in sous_etape or "texteAssocie" in sous_etape:
                    # there is no multiple depot in the National Assembly
                    # simply the senate re-submitting the same text
                    if data['steps']:
                        last_step = data['steps'][-1]
                        if last_step['institution'] == 'assemblee' and last_step.get('step') == step.get('step') == 'depot':
                            # ignore the depot we already have (since the new one is the same)
                            data['steps'] = data['steps'][:-1]

                    # step['xsi-type'] = sous_etape.get('@xsi:type')
                    # step['code'] = sous_etape.get('codeActe')

                    id_text = sous_etape.get("texteAdopte") or sous_etape.get("texteAssocie")
                    if id_text:
                        if "proposal_type" not in data:
                            if id_text.startswith("PRJL"):
                                data["proposal_type"] = "PJL"
                            elif id_text.startswith("PION"):
                                data["proposal_type"] = "PPL"

                        doc = {}
                        if id_text in docs:
                            doc = docs[id_text]
                        else:
                            _log("  - ERROR missing text", id_text)

                        url = None
                        if step.get("institution") == "assemblee" or "-AN" in code:
                            doc_code = None
                            if doc:
                                doc_code = doc['classification']['type']['code']
                                if doc_code == 'ACIN':
                                    continue
                            url = an_text_url(id_text, doc_code)
                            if url:
                                step['source_url'] = url

                    data["steps"].append(step)

                else:
                    pass

        if data['steps']:
            # add predicted step
            if not data.get('url_jo'):
                if data['steps'][-1].get('step') != start_step.get('step') and start_step.get('step'):
                    # TODO: we could also add all the dates into a steps['dates'] = [..]
                    data['steps'].append(start_step)
            data["beginning"] = data["steps"][0]["date"]
        else:
            _log("  - WARNING no steps found for", url)

        return data
    return []


if __name__ == "__main__":
    enable_requests_cache()
    url = sys.argv[1]
    data = parse(url)
    print(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False))
