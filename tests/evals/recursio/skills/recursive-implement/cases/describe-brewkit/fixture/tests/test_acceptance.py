# Copyright (c) 2026 The brewkit authors.
"""Acceptance tests for brewkit, as the README specifies."""

import re

import pytest

from brewkit.bitterness import ibu
from brewkit.cli import main
from brewkit.colour import describe, srm
from brewkit.gravity import abv, final_gravity, original_gravity
from brewkit.recipe import Grain, Hop, RecipeError, format_recipe, parse_recipe

RECIPE = """name: Garden Pale
batch: 20          # litres
efficiency: 72

grain: Pale malt, 4.5, 300, 3
grain: Crystal 60, 0.3, 280, 60
hop: Magnum, 20, 12.0, 60
hop: Cascade, 30, 6.5, 10   # late
"""


@pytest.fixture
def recipe_file(tmp_path):
    path = tmp_path / "pale.txt"
    path.write_text(RECIPE)
    return path


def test_parse_recipe():
    recipe = parse_recipe(RECIPE)
    assert (recipe.name, recipe.batch, recipe.efficiency) == ("Garden Pale", 20, 72)
    assert recipe.grains == [Grain("Pale malt", 4.5, 300, 3), Grain("Crystal 60", 0.3, 280, 60)]
    assert recipe.hops == [Hop("Magnum", 20, 12.0, 60), Hop("Cascade", 30, 6.5, 10)]


def test_bad_line_names_its_number():
    with pytest.raises(RecipeError, match=r"^line 3: "):
        parse_recipe("name: x\nbatch: 20\ngrain: Pale malt, lots, 300, 3\nefficiency: 70\n")


def test_missing_key_is_named():
    with pytest.raises(RecipeError, match="efficiency"):
        parse_recipe("name: x\nbatch: 20\n")


def test_gravity():
    og = original_gravity(parse_recipe(RECIPE))
    assert og == 1.052
    assert final_gravity(og, 75) == 1.013


def test_abv_is_in_the_right_range():
    assert abv(1.050, 1.050) == 0
    assert 5.0 <= abv(1.050, 1.010) <= 5.5


def test_ibu_tinseth():
    assert ibu(parse_recipe(RECIPE), 1.052) == 35.2


def test_srm_morey():
    assert srm(parse_recipe(RECIPE)) == 8.7
    assert [describe(x) for x in (2, 4, 14.9, 15, 40)] == ["straw", "gold", "amber", "brown", "black"]


def test_format_recipe_reads_back():
    recipe = parse_recipe(RECIPE)
    assert parse_recipe(format_recipe(recipe)) == recipe


def test_cli_stats(recipe_file, capsys):
    assert main(["stats", str(recipe_file)]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 5
    assert lines[0:2] == ["og: 1.052", "fg: 1.013"]
    assert re.fullmatch(r"abv: \d+\.\d%", lines[2])
    assert lines[3:] == ["ibu: 35.2", "srm: 8.7 (amber)"]


def test_cli_stats_attenuation(recipe_file, capsys):
    assert main(["stats", str(recipe_file), "--attenuation", "50"]) == 0
    assert capsys.readouterr().out.splitlines()[1] == "fg: 1.026"


def test_cli_scale(recipe_file, capsys):
    assert main(["scale", str(recipe_file), "--batch", "10"]) == 0
    assert capsys.readouterr().out == (
        "name: Garden Pale\nbatch: 10\nefficiency: 72\n"
        "grain: Pale malt, 2.250, 300, 3\ngrain: Crystal 60, 0.150, 280, 60\n"
        "hop: Magnum, 10.0, 12, 60\nhop: Cascade, 15.0, 6.5, 10\n"
    )


def test_cli_bad_recipe_exits_2(tmp_path, capsys):
    path = tmp_path / "bad.txt"
    path.write_text("name: x\ncolour: dark\n")
    assert main(["stats", str(path)]) == 2
    assert capsys.readouterr().err.startswith("brewkit: line 2: ")
