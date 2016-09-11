.. ANpy documentation master file, created by
   sphinx-quickstart on Sat Sep 10 14:45:09 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

ANpy: Scrape painlessly Assemblée Nationale website!
==========================================================

Release v\ |version|. (:ref:`Installation <install>`)

Forget the ugly html, just get data::

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

Supported Features
------------------

ANpy currently provides the following features:

- Amendement parsing
- Amendement search
- Question parsing
- Question search
- Dossier parsing

ANpy supports Python 2.7 & 3.5.

The User Guide
--------------

.. toctree::
   :maxdepth: 2

   user/intro
   user/install
   user/quickstart