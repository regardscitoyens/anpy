# ANpy: Scrape painlessly Assemblée Nationale website
[![PyPI version](https://badge.fury.io/py/anpy.svg)](https://badge.fury.io/py/anpy)
[![Build Status](https://travis-ci.org/regardscitoyens/anpy.svg)](https://travis-ci.org/regardscitoyens/anpy)

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
- Dossier parsing
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

* Show an amendement given its url :
```bash
python anpy-cli show_amendement http://www.assemblee-nationale.fr/14/amendements/1847/CION-DVP/CD266.asp
```

* Show amendements summaries after a given date :
```bash
python anpy-cli show_amendements_summary --start-date 2014-06-01
```

* Print amendements order for a given id_dossier and id_examen :
```bash
python anpy-cli show_amendements_order 33299 --id-examen 4073
```

* Show a question
```bash
python anpy-cli show_question http://questions.assemblee-nationale.fr/q14/14-73499QE.htm
```

* Show a dossier
```bash
python anpy-cli show_dossier http://www.assemblee-nationale.fr/14/dossiers/sante.asp
```

* Show a scrutin
```bash
python anpy-cli show_scrutin http://www2.assemblee-nationale.fr/scrutins/detail/(legislature)/14/(num)/1212
