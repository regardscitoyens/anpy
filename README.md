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
anpy-cli show_amendement http://www.assemblee-nationale.fr/14/amendements/1847/CION-DVP/CD266.asp
```

* Show amendements summaries after a given date :
```bash
anpy-cli show_amendements_summary --start-date 2014-06-01
```

* Print amendements order for a given id_dossier and id_examen :
```bash
anpy-cli show_amendements_order 33299 --id-examen 4073
```

* Show a question
```bash
anpy-cli show_question http://questions.assemblee-nationale.fr/q14/14-73499QE.htm
```

* Show a dossier
```bash
anpy-cli show_dossier http://www.assemblee-nationale.fr/14/dossiers/sante.asp
```

* Show a dossier formatted like [senapy](https://github.com/regardscitoyens/senapy)
```bash
anpy-cli show_dossier_like_senapy http://www.assemblee-nationale.fr/14/dossiers/sante.asp
```

* Find all the dossier urls
```bash
anpy-cli doslegs_url
```

* Parse many dossiers like senapy
```bash
cat urls | anpy-cli parse_many_doslegs output_dir
```

* Show a scrutin
```bash
anpy-cli show_scrutin http://www2.assemblee-nationale.fr/scrutins/detail/(legislature)/14/(num)/1212
```
