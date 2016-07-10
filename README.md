# ANpy
A python client of the "api" of http://assemblee-nationale.fr website

[![Build Status](https://travis-ci.org/fmassot/rc-tools.svg)](https://travis-ci.org/fmassot/anpy)

## Main goal
Retrieve painlessly json data from assemblee-nationale.fr

## Install :
```bash
pip install anpy
```

## Search services
Currently, only two search services are provided :
 * **AmendementSearchService** to search for amendements
 * **QuestionSearchService** to search for questions

## Models
There is no real api provided by http://assemblee-nationale.fr so there is no real data model exposed by the website.
It is sometimes hard to remember what you can get from the response, so I chose to declare all parsed data fields in models even if it's quite heavy just because it's easier to remember them...

Python classes used are *Amendement*, **AmendementSummary**, **AmendementSearchResult**, **QuestionSummary** and **QuestionSearchResult**.


## CLI
A script anpy-cli.py is installed with the package, it provides the following commands :

* Show an amendement given its url :
```bash
python anpy-cli.py show_amendement http://www.assemblee-nationale.fr/14/amendements/1847/CION-DVP/CD266.asp
```

* Show amendements summaries after a given date :
```bash
python anpy-cli.py show_amendements_summary --start-date 2014-06-01
```

* Print amendements order for a given id_dossier and id_examen :
```bash
python anpy-cli.py show_amendements_order 33299 4073
```

* Show a question
```bash
python anpy-cli.py show_question http://questions.assemblee-nationale.fr/q14/14-73499QE.htm
```