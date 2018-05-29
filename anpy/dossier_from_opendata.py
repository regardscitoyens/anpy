"""
Experiment to use the JSON formatted data provided byt the AN for the doslegs

  - step 1: download the data needed here:
  http://data.assemblee-nationale.fr/static/openData/repository/15/loi/dossiers_legislatifs/Dossiers_Legislatifs_XV.json.zip
  - step 2: you can parse a dosleg by doing
  python dossier_from_opendata.py dossiers.json <dosleg_url>
"""

import sys
import json

from lawfactory_utils.urls import download, enable_requests_cache, clean_url


def _log(*args):
    print(*args, file=sys.stderr)


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


def parse(url, dossiers_json):
    docs = {
        doc["uid"]: doc
        for doc in dossiers_json["export"]["textesLegislatifs"]["document"]
    }

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
        data["url_dossier_senat"] = dossier["titreDossier"]["senatChemin"]
        data["long_title"] = dossier["titreDossier"]["titre"]
        data["url_dossier_assemblee"] = url
        data["assemblee_legislature"] = int(dossier["legislature"])
        data["assemblee_slug"] = dossier["titreDossier"]["titreChemin"]
        data["assemblee_id"] = "%s-%s" % (
            dossier["legislature"],
            data["assemblee_slug"],
        )

        data["steps"] = []
        for etape in to_arr(dossier["actesLegislatifs"]["acteLegislatif"]):
            for path, sous_etape in yield_leafs(etape):
                if sous_etape["@xsi:type"] in ("EtudeImpact_Type",):
                    continue

                step = {"date": sous_etape.get("dateActe").split("T")[0]}

                if sous_etape["@xsi:type"] == "ProcedureAccelere_Type":
                    data["urgence"] = True
                elif sous_etape["@xsi:type"] == "Promulgation_Type":
                    url = clean_url(sous_etape["urlLegifrance"])
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
                    sous_etape["texteAssocie"] = sous_etape["textesAssocies"][
                        "texteAssocie"
                    ]["refTexteAssocie"]

                if "texteAdopte" in sous_etape or "texteAssocie" in sous_etape:
                    code = sous_etape.get("codeActe")

                    if code.startswith("AN"):
                        step["institution"] = "assemblee"
                    elif code.startswith("SN"):
                        step["institution"] = "senat"

                    if "-DEPOT" in code:
                        step["step"] = "depot"
                    elif "-COM" in code:
                        step["step"] = "commission"
                    elif "-DEBATS-DEC" in code:
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
                        if "RAPPORT-AN" in code:
                            step["institution"] = "assemblee"
                        elif "RAPPORT-SN" in code:
                            step["institution"] = "senat"
                            continue  #  TODO: add link to CMP commission step
                        else:
                            step["institution"] = "CMP"

                    # step['xsi-type'] = sous_etape.get('@xsi:type')
                    # step['code'] = sous_etape.get('codeActe')

                    id_text = sous_etape.get("texteAdopte", sous_etape["texteAssocie"])
                    if id_text:
                        if "proposal_type" not in data:
                            if id_text.startswith("PRJL"):
                                data["proposal_type"] = "PJL"
                            elif id_text.startswith("PION"):
                                data["proposal_type"] = "PPL"

                        if step.get("institution") == "assemblee" and id_text:
                            text_no = id_text[-4:]

                            url = None
                            if step.get("step") == "commission":
                                if step.get("stage") == "CMP":
                                    url = (
                                        "http://www.assemblee-nationale.fr/{}/rapport/{}.asp"
                                    )
                                else:
                                    url = (
                                        "http://www.assemblee-nationale.fr/{}/ta-commission/r{}-a0.asp"
                                    )
                            elif step.get("step") == "depot":
                                if data["proposal_type"] == "PJL":
                                    url = (
                                        "http://www.assemblee-nationale.fr/{}/projets/pl{}.asp"
                                    )
                                else:
                                    url = (
                                        "http://www.assemblee-nationale.fr/{}/propositions/pion{}.asp"
                                    )
                            elif step.get("step") == "hemicycle":
                                url = "http://www.assemblee-nationale.fr/{}/ta/ta{}.asp"

                            if url:
                                doc = {}
                                if id_text in docs:
                                    doc = docs[id_text]
                                else:
                                    _log("  - ERROR missing text", id_text)
                                legislature = doc.get(
                                    "legislature", data["assemblee_legislature"]
                                )
                                url = url.format(legislature, text_no)
                                step["source_url"] = url

                            if not url or not test_status(url):
                                _log("  - INVALID text url -", url, step)
                                _log()
                        #  TODO: url senat
                        #  TODO: url CMP + other url
                    data["steps"].append(step)

                else:
                    pass
        data["beggining"] = data["steps"][0]["date"]

        return data


if __name__ == "__main__":
    enable_requests_cache()
    dossiers_json = json.load(open(sys.argv[1]))  # TODO: automate the download
    url = sys.argv[2]
    data = parse(url, dossiers_json)
    print(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False))
