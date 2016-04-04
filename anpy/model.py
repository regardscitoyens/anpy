# -*- coding: utf-8 -*-


class Amendement(object):
    def __init__(self, url=None, num_amtxt=None, amend_parent=None, url_dossier=None, num_init=None, etape=None,
                 deliberation=None, titre_init=None, num_partie=None, designation_article=None, url_division=None,
                 designation_alinea=None, mission=None, auteurs=None, auteur_id=None, groupe_id=None,
                 cosignataires_id=None, seance=None, sort=None, date_badage=None, date_sort=None, ordre_texte=None,
                 code=None, refcode=None, legislature=None, dispositif=None, expose=None, num_amend=None):
        self.url = url
        self.num_amtxt = num_amtxt
        self.amend_parent = amend_parent
        self.url_dossier = url_dossier
        self.num_init = num_init
        self.etape = etape
        self.deliberation = deliberation
        self.titre_init = titre_init
        self.num_partie = num_partie
        self.designation_article = designation_article
        self.url_division = url_division
        self.designation_alinea = designation_alinea
        self.mission = mission
        self.auteurs = auteurs
        self.auteur_id = auteur_id
        self.groupe_id = groupe_id
        self.cosignataires_id = cosignataires_id
        self.seance = seance
        self.sort = sort
        self.date_badage = date_badage
        self.date_sort = date_sort
        self.ordre_texte = ordre_texte
        self.code = code
        self.refcode = refcode
        self.legislature = legislature
        self.dispositif = dispositif
        self.expose = expose
        self.num_amend = num_amend


class AmendementSummary(object):
    def __init__(self, id=None, num_init=None, titre_dossier_legislatif=None, url_dossier_legislatif=None, instance=None, num_amend=None,
                 url_amend=None, designation_article=None, designation_alinea=None, date_depot=None, signataires=None,
                 sort=None, legislature=None, mission_visee=None):
        self.id = id
        self.num_init = num_init
        self.titre_dossier_legislatif = titre_dossier_legislatif
        self.url_dossier_legislatif = url_dossier_legislatif
        self.instance = instance
        self.num_amend = num_amend
        self.url_amend = url_amend
        self.designation_article = designation_article
        self.designation_alinea = designation_alinea
        self.date_depot = date_depot
        self.signataires = signataires
        self.sort = sort
        self.legislature = legislature
        self.mission_visee = mission_visee

    def __repr__(self):
        return self.__dict__.__repr__()


class AmendementSearchResult(object):
    def __init__(self, url=None, total_count=None, start=None, size=None, results=None):
        self.url = url
        self.total_count = total_count
        self.start = start
        self.size = size
        self.results = results

    def __repr__(self):
        return self.__dict__.__repr__()
        
        
class QuestionSummary(object):
    def __init__(self, url=None, legislature=None, numero=None, question_type=None, author=None, tags=None, publication_date=None, answer_date=None):
        self.url = url
        self.legislature = legislature
        self.numero = numero
        self.question_type = question_type
        self.author = author
        self.tags = tags
        self.publication_date = publication_date
        self.answer_date = answer_date

    def __repr__(self):
        return self.__dict__.__repr__()
        

class QuestionSearchResult(object):
    def __init__(self, url=None, total_count=None, next_url=None, size=None, results=None):
        self.url = url
        self.total_count = total_count
        self.next_url = next_url
        self.size = size
        self.results = results

    def __repr__(self):
        return self.__dict__.__repr__()