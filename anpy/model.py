# -*- coding: utf-8 -*-
import attr
from enum import Enum


@attr.s
class TT(object):
    url = attr.ib(default=None)

@attr.s
class Amendement(object):
    url = attr.ib(default=None)
    num_amtxt = attr.ib(default=None)
    amend_parent = attr.ib(default=None)
    url_dossier = attr.ib(default=None)
    num_init = attr.ib(default=None)
    etape = attr.ib(default=None)
    deliberation = attr.ib(default=None)
    titre_init = attr.ib(default=None)
    num_partie = attr.ib(default=None)
    designation_article = attr.ib(default=None)
    url_division = attr.ib(default=None)
    designation_alinea = attr.ib(default=None)
    mission = attr.ib(default=None)
    auteurs = attr.ib(default=None)
    auteur_id = attr.ib(default=None)
    groupe_id = attr.ib(default=None)
    cosignataires_id = attr.ib(default=None)
    seance = attr.ib(default=None)
    sort = attr.ib(default=None)
    date_badage = attr.ib(default=None)
    date_sort = attr.ib(default=None)
    ordre_texte = attr.ib(default=None)
    code = attr.ib(default=None)
    refcode = attr.ib(default=None)
    legislature = attr.ib(default=None)
    dispositif = attr.ib(default=None)
    expose = attr.ib(default=None)
    num_amend = attr.ib(default=None)


@attr.s
class AmendementSummary(object):
    id = attr.ib(default=None)
    num_init = attr.ib(default=None)
    titre_dossier_legislatif = attr.ib(default=None)
    url_dossier_legislatif = attr.ib(default=None)
    instance = attr.ib(default=None)
    num_amend = attr.ib(default=None)
    url_amend = attr.ib(default=None)
    designation_article = attr.ib(default=None)
    designation_alinea = attr.ib(default=None)
    date_depot = attr.ib(default=None)
    signataires = attr.ib(default=None)
    sort = attr.ib(default=None)
    legislature = attr.ib(default=None)
    mission_visee = attr.ib(default=None)


@attr.s
class AmendementSearchResult(object):
    url = attr.ib(default=None)
    total_count = attr.ib(default=None)
    start = attr.ib(default=None)
    size = attr.ib(default=None)
    results = attr.ib(default=None)


@attr.s
class QuestionSummary(object):
    url = attr.ib(default=None)
    legislature = attr.ib(default=None)
    numero = attr.ib(default=None)
    question_type = attr.ib(default=None)
    author = attr.ib(default=None)
    tags = attr.ib(default=None)
    publication_date = attr.ib(default=None)
    answer_date = attr.ib(default=None)


@attr.s
class QuestionSearchResult(object):
    url = attr.ib(default=None)
    total_count = attr.ib(default=None)
    next_url = attr.ib(default=None)
    size = attr.ib(default=None)
    results = attr.ib(default=None)


class ProcedureParlementaire(Enum):
    PJL = 'PJL'
    PPL = 'PPL'


class LegislativeStep(Enum):
    AN_PREMIERE_LECTURE = 'AN_PREMIERE_LECTURE'
    SENAT_PREMIERE_LECTURE = 'SENAT_PREMIERE_LECTURE'
    CMP = 'CMP'
    CONSEIL_CONSTIT = 'CONSEIL_CONSTITUT'
    AN_NOUVELLE_LECTURE = 'AN_NOUVELLE_LECTURE'
    SENAT_NOUVELLE_LECTURE = 'SENAT_NOUVELLE_LECTURE'
    AN_LECTURE_DEFINITIVE = 'AN_LECTURE_DEFINITIVE'


class DecisionStatus(Enum):
    ADOPTED = 'ADOPTED'
    REJECTED = 'REJECTED'
    MODIFIED = 'MODIFIED'


class LegislativeAct(Enum):
    ETUDE_IMPACT = 'ETUDE_IMPACT'
    AVIS_CONSEIL_ETAT = 'AVIS_CONSEIL_DETAT'
    PROCEDURE_ACCELEREE = 'PROCEDURE_ACCELEREE'
    REUNION_COMMISSION = 'REUNION_COMMISSION'
    DISCUSSION_COMMISSION = 'DISCUSSION_COMMISSION'
    DEPOT_RAPPORT = 'DEPOT_RAPPORT'
    SAISIE_COM_AVIS = 'SAISIE_COM_AVIS'
    NOMINATION_RAPPORTEURS = 'NOMINATION_RAPPORTEURS'
    DISCUSSION_SEANCE_PUBLIQUE = 'DISCUSSION_SEANCE_PUBLIQUE'
    DECISION = 'DECISION'
    DEPOT_INITIATIVE = 'DEPOT_INITIATIVE'
    SAISIE_COM_FOND = 'SAISIE_COM_FOND'
    PROMULGATION = 'PROMULGATION'
    SAISINE_CONSEIL_CONSTIT = 'SAISINE_CONSEIL_CONSTIT'
