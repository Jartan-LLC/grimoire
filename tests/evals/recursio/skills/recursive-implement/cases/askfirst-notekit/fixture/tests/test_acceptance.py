# SPDX-License-Identifier: MIT
"""Acceptance tests for notekit, as the README specifies."""

import pytest

from notekit.cli import main
from notekit.links import backlinks, broken, links
from notekit.notes import load_notes
from notekit.tags import tag_index, tags

NOTES = {
    "alpha.md": "# Alpha\n\nSee [[beta]] and [[gamma|the third]]. #Ideas #draft\n",
    "beta.md": "# Beta\n\nBack to [[alpha]]; again [[alpha]], then [[missing]].\n#ideas, and page#anchor\n",
    "gamma.md": "No heading here, just words #draft-2\n",
    "todo.txt": "not a note [[alpha]] #ideas\n",
}


@pytest.fixture
def folder(tmp_path):
    for name, text in NOTES.items():
        (tmp_path / name).write_text(text)
    (tmp_path / "archive").mkdir()
    (tmp_path / "archive" / "old.md").write_text("# Old\n[[alpha]]\n")
    return tmp_path


def test_load_notes(folder):
    notes = load_notes(folder)
    assert [(n.name, n.title) for n in notes] == [("alpha", "Alpha"), ("beta", "Beta"), ("gamma", "gamma")]
    assert notes[2].words == 6
    assert notes[0].meta == {}


def test_tags(folder):
    alpha, beta, gamma = load_notes(folder)
    assert tags(alpha) == {"ideas", "draft"}
    assert tags(beta) == {"ideas"}
    assert tags(gamma) == {"draft-2"}


def test_tag_index(folder):
    assert tag_index(load_notes(folder)) == {"draft": ["alpha"], "draft-2": ["gamma"], "ideas": ["alpha", "beta"]}


def test_links_in_order_each_once(folder):
    alpha, beta, _ = load_notes(folder)
    assert links(alpha) == ["beta", "gamma"]
    assert links(beta) == ["alpha", "missing"]


def test_backlinks_and_broken(folder):
    notes = load_notes(folder)
    assert backlinks(notes) == {"alpha": ["beta"], "beta": ["alpha"], "gamma": ["alpha"]}
    assert broken(notes) == [("beta", "missing")]


def test_cli_tags(folder, capsys):
    assert main(["tags", str(folder)]) == 0
    assert capsys.readouterr().out == "draft: alpha\ndraft-2: gamma\nideas: alpha, beta\n"


def test_cli_backlinks(folder, capsys):
    assert main(["backlinks", str(folder), "alpha"]) == 0
    assert capsys.readouterr().out == "beta\n"
    assert main(["backlinks", str(folder), "nope"]) == 1


def test_cli_broken(folder, capsys):
    assert main(["broken", str(folder)]) == 1
    assert capsys.readouterr().out == "beta -> missing\n"
