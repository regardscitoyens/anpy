#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import sys
from pathlib import Path

import attr
import click
import requests

from anpy.dossier import DossierParser
from anpy.question import parse_question
from anpy.amendement import parse_amendement, AmendementSearchService
from anpy.utils.json_utils import json_dumps

sys.path.append(str(Path(__file__).absolute().parents[1]))


@click.group()
def cli():
    pass


@cli.command()
@click.argument('id-dossier')
@click.option('--id-examen')
@click.option('--limit', default=100)
def show_amendements_order(id_dossier, id_examen, limit):
    results = AmendementSearchService().get_order(
        idDossierLegislatif=id_dossier, idExamen=id_examen, rows=limit)
    print('Nombre d\'amendements   : {}'.format(len(results)))
    print('Ordre des ammendements : {}'.format((','.join(results))))


@cli.command()
@click.option('--start-date')
@click.option('--end-date')
@click.option('--numero')
@click.option('--rows', default=100)
def show_amendements_summary(start_date, end_date, numero, rows):
    iterator = AmendementSearchService().iterator(rows=rows,
                                                  dateDebut=start_date,
                                                  dateFin=end_date,
                                                  numAmend=numero)
    for result in iterator:
        print(json.dumps(attr.asdict(result), indent=4, sort_keys=True,
                         ensure_ascii=False))


@cli.command()
@click.argument('url')
def show_amendement(url):
    print('Amendement : {}'.format(url))
    print(json.dumps(parse_amendement(url, requests.get(url).content).__dict__,
                     indent=4, sort_keys=True, ensure_ascii=False))


@cli.command()
@click.argument('url')
def show_question(url):
    question_html = requests.get(url + '/vue/xml').content
    parsed_data = parse_question(url, question_html)
    print(json.dumps(parsed_data, indent=4, sort_keys=True,
                     ensure_ascii=False))


@cli.command()
@click.argument('url')
def show_dossier(url):
    html = requests.get(url).content
    dossier = DossierParser(url, html).parse()
    print(json_dumps(dossier.to_dict(), indent=4, sort_keys=True,
                     ensure_ascii=False))

if __name__ == '__main__':
    cli()
