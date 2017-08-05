from devdocs_cli.__main__ import priority


def test_priority_no_match():
    assert priority(('sample', 'samsple'), 'dummy sample test') == 0


def test_priority_match():
    assert priority(('test', 'sample'), 'dummy sample test') == 1


def test_priority_starts_match():
    assert priority(('dummy', 'sample'), 'dummy sample test') == 2
