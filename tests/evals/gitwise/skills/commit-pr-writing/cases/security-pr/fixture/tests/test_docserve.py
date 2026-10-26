from docserve import read_doc


def test_reads_a_doc() -> None:
    assert read_doc("intro.md") == "# Intro\n"
