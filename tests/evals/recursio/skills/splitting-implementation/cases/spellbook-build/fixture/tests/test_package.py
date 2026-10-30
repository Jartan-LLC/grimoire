import pathlib

import spellbook


def test_bundled_list_ships():
    words = pathlib.Path(spellbook.__file__).parent / "words" / "en.txt"
    assert "configuration" in words.read_text()
