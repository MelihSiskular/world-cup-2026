import wc26


def test_package_has_version() -> None:
    assert isinstance(wc26.__version__, str)
    assert wc26.__version__
