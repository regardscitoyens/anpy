.. _quickstart:

Quickstart
==========

Let's get started with some simple examples.

Get dossier data
----------------

First find some 'dossier' of a given law from assemblee-nationale.fr,
for example `the one about the numeric law voted in 2016`_::

    >>> from anpy.dossier import Dossier
    >>> url = 'http://www.assemblee-nationale.fr/14/dossiers/republique_numerique.asp'
    >>> dossier = Dossier.download_and_build(url)
    >>> dossier.title
    'Economie : pour une République numérique'


We can list of the legislative steps made for this law::

    >>> [s['type'] for s in dossier.steps]
    ['AN_PREMIERE_LECTURE', 'SENAT_PREMIERE_LECTURE', 'CMP']

Moreover, it's easy to get the different law versions (url and date) voted by members of parliaments::

    >>> [act['url'] for s in dossier.steps
         for act in s['acts'] if act['type'] == 'DEPOT_INITIATIVE']
    ['http://www.assemblee-nationale.fr/14/projets/pl3318.asp',
    'http://www.senat.fr/leg/pjl15-325.html',
    'http://www.assemblee-nationale.fr/14/projets/pl3724.asp']
    >>> [act['date'] for s in dossier.steps
         for act in s['acts'] if act['type'] == 'DEPOT_INITIATIVE']
    [datetime.datetime(2015, 12, 9, 0, 0),
     datetime.datetime(2016, 1, 26, 0, 0),
     datetime.datetime(2016, 5, 4, 0, 0)]

.. _the one about the numeric law voted in 2016: http://www.assemblee-nationale.fr/14/dossiers/republique_numerique.asp

Get amendement data
-------------------

First find some amendement from assemblee-nationale.fr, for example `this one`_::

    >>> from anpy.amendement import Amendement

Now let's download it and see what's in it::

    >>> a = Amendement.download_and_build('http://www.assemblee-nationale.fr/14/amendements/0922/AN/406.asp')
    >>> a.titre_init
    'OUVERTURE DU MARIAGE AUX COUPLES DE MÊME SEXE(n°922)'
    >>> a.auteurs
    'Mme Louwagie et Mme Marianne Dubois'


.. _this one: http://www.assemblee-nationale.fr/14/amendements/0922/AN/406.asp

Search for amendement
---------------------

assemblee-nationale.fr provides an amendement search engine which uses a json API, ANpy directly uses this API::

    >>> from anpy.amendement import AmendementSearchService

Let's say we want to get a preview of all amendements written between January 2014 and March 2014::

    >>> params = {'dateDebut': '2014-01-01', 'dateFin': '2014-02-01', 'size': 10}
    >>> service = AmendementSearchService()
    >>> service.total_count(**params)
    4171
    >>> first_page = next(service.iterator(**params))
    >>> first_page.size
    10
    >>> first_page.results[0]
    AmendementSummary(id='S-AMANR5L14PO419610B1338N93', num_init='1338', ...)


Note that this service returns only partial data of an amendement, if you want to get all the data especially the variables
'expose' and 'dispositif', you have to download the amendement html page::
    >>> from anpy.amendement import Amendement
    >>> Amendement.download_and_build(first_page.results[0].url).expose
    '<p>Cet amendement propose d\'interdire des clauses dérogatoires...'

To get all the page results, just call list()::
    >>> all_pages = list(service.iterator(**params))


Get question data
-----------------

TODO

Search for question
-------------------

TODO