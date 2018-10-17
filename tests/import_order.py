import pytest


def test_presamples_import_first():
    import presamples
    from bw2calc.lca import PackagesDataLoader
    assert PackagesDataLoader is not None

def test_bw2calc_import_first():
    from bw2calc.lca import PackagesDataLoader
    import presamples
    assert PackagesDataLoader is not None
