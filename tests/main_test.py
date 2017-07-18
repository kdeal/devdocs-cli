from devdocs_cli.__main__ import priority


def test_priority_no_match():
    assert priority('samsple', 'dummy sample test') == 0


def test_priority_match():
    assert priority('sample', 'dummy sample test') == 1


def test_priority_starts_match():
    assert priority('dummy', 'dummy sample test') == 2
