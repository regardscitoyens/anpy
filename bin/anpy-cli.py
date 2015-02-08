# -*- coding: utf-8 -*-
#!/usr/bin/env python

import sys
import json

import click
import requests
from pathlib import Path

sys.path.append(str(Path(__file__).absolute().parents[1]))

from anpy.service import AmendementSearchService
from anpy.parsing.question_parser import parse_question
from anpy.parsing.amendement_parser import parse_amendement


@click.group()
def cli():
    pass


@cli.command()
@click.argument('id-dossier')
@click.option('--id-examen')
@click.option('--limit', default=100)
def show_amendements_order(id_dossier, id_examen, limit):
    results = AmendementSearchService().get_order(idDossierLegislatif=id_dossier, idExamen=id_examen, rows=limit)
    print('Nombre d\'amendements   : {}'.format(len(results)))
    print('Ordre des ammendements : {}'.format((','.join(results))))


@cli.command()
@click.option('--start-date')
@click.option('--end-date')
@click.option('--numero')
@click.option('--rows', default=100)
def show_amendements_summary(start_date, end_date, numero, rows):
    iterator = AmendementSearchService().iter(rows=rows, dateDebut=start_date, dateFin=end_date, numAmend=numero)
    for result in iterator:
        print(json.dumps(result.__dict__, indent=4, sort_keys=True, ensure_ascii=False))


@cli.command()
@click.argument('url')
def show_amendement(url):
    print('Amendement : {}'.format(url))
    print(json.dumps(parse_amendement(url, requests.get(url).content).__dict__, indent=4, sort_keys=True, ensure_ascii=False))


@cli.command()
@click.argument('url')
def show_question(url):
    question_html = requests.get(url).content
    parsed_data = parse_question(url, question_html)
    print(json.dumps(parsed_data, indent=4, sort_keys=True, ensure_ascii=False))


if __name__ == '__main__':
    cli()
