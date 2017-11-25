from anpy.amendement import AmendementSearchService


def test_get():
    service = AmendementSearchService()

    assert 2 == len(service.get(idDossierLegislatif=31515, idExamen=3295, rows=2).results)


def test_total_count():
    service = AmendementSearchService()
    assert 5 == service.total_count(rows=1, idDossierLegislatif=31515, idExamen=3295)


def test_iterator():
    service = AmendementSearchService()
    iterator = service.iterator(idDossierLegislatif=31515, idExamen=3295, rows=2)
    next(iterator)
    next(iterator)
    last_page_result = next(iterator)

    assert 1 == len(last_page_result.results)


def test_get_order():
    service = AmendementSearchService()
    order = service.get_order(idDossierLegislatif=31515, idExamen=3295, rows=2)
    assert order == ['CD4', 'CD13', 'CD1', 'CD3', 'CD2']
