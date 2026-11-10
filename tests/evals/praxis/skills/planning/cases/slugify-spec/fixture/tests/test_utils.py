from utils import title_case


def test_title_case():
    assert title_case('a b') == 'A B'
