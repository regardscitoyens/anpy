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
 * **QuestionService** to search for questions

## Models
All results coming from http://assemblee-nationale.fr are parsed and instanciate custom python classes *Amendement*, **AmendementSummary**, **AmendementSearchResult**, **QuestionSummary** and **QuestionSearchResult**.
The idea was to declare all data fields provided by website because it's easier to remember them... the consistency of variables' names coming fromassemblee-nationale.fr is not always easy to understand.

## CLI
A script anpy-cli.py is installed with the package, it provides the following commands :

* Show an amendement given its url :
```python
python anpy-cli.py show_amendement http://www.assemblee-nationale.fr/14/amendements/1847/CION-DVP/CD266.asp
```

* Show amendements summaries after a given date :
```python
python anpy-cli.py show_amendements_summary --start-date 2014-06-01
```

* Print amendements order for a given id_dossier and id_examen :
```python
python anpy-cli.py show_amendements_order 33299 4073
```

* Show a question
```python
python anpy-cli.py show_question http://questions.assemblee-nationale.fr/q14/14-73499QE.htm
```