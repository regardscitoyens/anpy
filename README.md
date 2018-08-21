# ANpy: Scrape painlessly Assemblée Nationale website
[![PyPI version](https://badge.fury.io/py/anpy.svg)](https://badge.fury.io/py/anpy)
[![Build Status](https://travis-ci.org/regardscitoyens/anpy.svg)](https://travis-ci.org/regardscitoyens/anpy)
[![Coverage Status](https://coveralls.io/repos/github/regardscitoyens/anpy/badge.svg?branch=master)](https://coveralls.io/github/regardscitoyens/anpy?branch=master)

ANpy is a python library for easily scraping data from http://assemblee-nationale.fr website

Forget the ugly html, just get data:

    >>> from anpy.dossier import Dossier
    >>> url = 'http://www.assemblee-nationale.fr/14/dossiers/republique_numerique.asp'
    >>> dossier = Dossier.download_and_build(url)
    >>> dossier.title
    'Economie : pour une République numérique'
    >>> dossier.legislature
    14
    >>> r.procedure
    'PPL'
    >>> r.senat_url
    'http://www.senat.fr/dossier-legislatif/pjl15-325.html'
    >>> r.steps
    [{'type': 'AN_PREMIERE_LECTURE', 'acts': [...]}]


## Supported Features

ANpy currently provides the following features:

- Amendement parsing
- Amendement search
- Question parsing
- Question search
- Dossier parsing (two differents formats)
- Scrutin parsing

ANpy supports Python 3.5.

## Install :
```bash
pip install anpy
```

## Documentation

Documentation is available at http://anpy.readthedocs.io/en/latest


## CLI
A script anpy-cli is installed with the package, it provides the following commands :

#### Show an amendement given its url
```bash
anpy-cli show_amendement http://www.assemblee-nationale.fr/14/amendements/1847/CION-DVP/CD266.asp
```

#### Show amendements summaries after a given date
```bash
anpy-cli show_amendements_summary --start-date 2014-06-01
```

#### Print amendements order for a given id_dossier and id_examen
```bash
anpy-cli show_amendements_order 33299 --id-examen 4073
```

#### Show a question
```bash
anpy-cli show_question http://questions.assemblee-nationale.fr/q14/14-73499QE.htm
```

#### Show a law project (dossier législatif)

Format is like [senapy](https://github.com/regardscitoyens/senapy) and the Open Data of [lafabriquedelaloi.fr](https://www.lafabriquedelaloi.fr)

*There's more work done on this parser to make it work across many cases*

```bash
anpy-cli parse http://www.assemblee-nationale.fr/14/dossiers/sante.asp
[
    {
        "assemblee_id": "14-sante",
        "assemblee_legislature": 14,
        "assemblee_slug": "sante",
        "beginning": "2014-10-15",
        "long_title": "Questions sociales et santé : modernisation de notre système de santé",
        "steps": [
            {
                "date": "2014-10-15",
                "institution": "assemblee",
                "source_url": "http://www.assemblee-nationale.fr/14/projets/pl2302.asp",
                "stage": "1ère lecture",
                "step": "depot"
            },
            {
                "date": "2015-03-20",
                "institution": "assemblee",
                "source_url": "http://www.assemblee-nationale.fr/14/ta-commission/r2673-a0.asp",
                "stage": "1ère lecture",
                "step": "commission"
            },
            {
                "date": "2015-04-14",
                "institution": "assemblee",
                "source_url": "http://www.assemblee-nationale.fr/14/ta/ta0505.asp",
                "stage": "1ère lecture",
                "step": "hemicycle"
            },
...
```

Features:
- Merging the law project across legislatures
- Parse from Open Data when available or fallback to scraping HTML
- Returns an array of law projects since a page can contains many law projects (ex: organic + non-organic)


You can also parse many of them by giving a list of urls:

```bash
anpy-cli doslegs_urls | anpy-cli parse_many an_doslegs/
```

#### Show a law project (with a format is similar to the AN Open Data)

*This parser is still a work-in-progress*

```bash
anpy-cli show_dossier http://www.assemblee-nationale.fr/14/dossiers/sante.asp
{
    "legislature": "14",
    "procedure": "PJL",
    "senat_url": "http://www.senat.fr/dossier-legislatif/pjl14-406.html",
    "steps": [
        {
            "acts": [
                {
                    "date": "2014-10-15T00:00:00",
                    "type": "DEPOT_INITIATIVE",
                    "url": "http://www.assemblee-nationale.fr/14/projets/pl2302.asp"
                },
                {
                    "type": "ETUDE_IMPACT",
                    "url": "http://www.assemblee-nationale.fr/14/projets/pl2302-ei.asp"
                },
                {
                    "date": "2015-03-16T00:00:00",
                    "type": "PROCEDURE_ACCELEREE"
                },
                {
                    "date": "2015-03-20T00:00:00",
                    "type": "DEPOT_RAPPORT",
                    "url": "http://www.assemblee-nationale.fr/14/rapports/r2673.asp"
                },
                {
                    "date": "2015-03-24T00:00:00",
                    "type": "TEXTE_COMMISSION",
                    "url": "http://www.assemblee-nationale.fr/14/ta-commission/r2673-a0.asp"
                },
                {
                    "date": "2015-02-11T00:00:00",
                    "type": "DEPOT_RAPPORT",
                    "url": "http://www.assemblee-nationale.fr/14/rap-info/i2581.asp"
                },
                {
...
```


#### Find all the dossier urls
```bash
anpy-cli doslegs_urls
```

#### Show a scrutin
```bash
anpy-cli show_scrutin http://www2.assemblee-nationale.fr/scrutins/detail/(legislature)/14/(num)/1212
```
