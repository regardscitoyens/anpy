"""
Experiment to use the JSON formatted data provided by the AN for the doslegs

  python dossier_from_opendata.py <dosleg_url>
"""

import sys
import json
import zipfile
import io
import re

from lawfactory_utils.urls import download, enable_requests_cache, clean_url
import lawfactory_utils.urls

from anpy.dossier import get_legislature


def yield_leafs(etape, path=None):
    if path is None:
        path = []
    if etape.get("actesLegislatifs"):
        for children in to_arr(etape["actesLegislatifs"]["acteLegislatif"]):
            yield from yield_leafs(children, path=path + [etape])
    else:
        yield path, etape


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


def download_open_data_doslegs(legislature):
    files = {
        15: (
            "Dossiers_Legislatifs_XV.json",
            "http://data.assemblee-nationale.fr/static/openData/repository/15/loi/dossiers_legislatifs/Dossiers_Legislatifs_XV.json.zip",
        ),
        14: (
            "Dossiers_Legislatifs_XIV.json",
            "http://data.assemblee-nationale.fr/static/openData/repository/14/loi/dossiers_legislatifs/Dossiers_Legislatifs_XIV.json.zip",
        ),
    }
    #  TODO: remove this hack when we are able to cache the zip files
    file, file_url = files[legislature]

    CACHE_ENABLED = lawfactory_utils.urls.CACHE_ENABLED
    lawfactory_utils.urls.CACHE_ENABLED = False
    doslegs_resp = download(file_url)
    lawfactory_utils.urls.CACHE_ENABLED = CACHE_ENABLED

    doslegs_zip = zipfile.ZipFile(io.BytesIO(doslegs_resp.content))
    DATA = json.loads(doslegs_zip.open(file).read().decode("utf-8"))

    return DATA


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
            'repertoire': 'europe/resolutions',
            'prefixe': 'ppe',
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
    return host + leg + "/" + datas[type]['repertoire'] + "/" + datas[type]['prefixe'] + num + datas[type]['suffixe'] + ".asp"


def parse(url, verbose=True, logfile=sys.stderr, cached_opendata_an={}):
    if not verbose:

        def _log(*x):
            return None

    else:

        def _log(*args):
            nonlocal logfile
            print(*args, file=logfile)

    legislature = get_legislature(url)
    if legislature and legislature in cached_opendata_an:
        dossiers_json = cached_opendata_an[legislature]
    else:
        dossiers_json = download_open_data_doslegs(get_legislature(url))

    docs = {doc["uid"]: doc for doc in dossiers_json["export"]["textesLegislatifs"]["document"]}

    for dossier in dossiers_json["export"]["dossiersLegislatifs"]["dossier"]:
        dossier = dossier["dossierParlementaire"]

        titreChemin = dossier["titreDossier"]["titreChemin"]

        # find the right dosleg even if it's an old url
        url_common_part = "{}/dossiers/{}".format(dossier["legislature"], titreChemin)
        if url_common_part not in url:
            continue
        url = "http://www.assemblee-nationale.fr/dyn/{}".format(url_common_part)

        data = {}
        data["urgence"] = False
        url_senat = dossier["titreDossier"]["senatChemin"]
        if url_senat:
            data["url_dossier_senat"] = url_senat
        data["long_title"] = dossier["titreDossier"]["titre"]
        data["url_dossier_assemblee"] = url
        data["assemblee_legislature"] = int(dossier["legislature"])
        data["assemblee_slug"] = dossier["titreDossier"]["titreChemin"]
        data["assemblee_id"] = "%s-%s" % (dossier["legislature"], data["assemblee_slug"])

        data["steps"] = []
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

                if "texteAdopte" in sous_etape or "texteAssocie" in sous_etape:
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
                    elif "-DEBATS-DEC" in code or "DEBATS-AN-DEC" in code or "DEBATS-SN-DEC" in code:
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

                    # step['xsi-type'] = sous_etape.get('@xsi:type')
                    # step['code'] = sous_etape.get('codeActe')
                    step["id_opendata"] = sous_etape["uid"]

                    id_text = sous_etape.get("texteAdopte", sous_etape["texteAssocie"])
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
                            url = an_text_url(id_text, doc_code)
                            if url:
                                step['source_url'] = url

                    data["steps"].append(step)

                else:
                    pass
        data["beggining"] = data["steps"][0]["date"]

        return data
    return []


if __name__ == "__main__":
    enable_requests_cache()
    url = sys.argv[1]
    data = parse(url)
    print(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False))
