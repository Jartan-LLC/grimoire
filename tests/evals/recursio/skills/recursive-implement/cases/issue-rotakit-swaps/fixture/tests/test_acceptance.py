"""Acceptance tests for issue 47, as the README specifies."""

from datetime import date

import pytest

from rotakit.cli import main
from rotakit.ical import to_ical
from rotakit.model import Person, Rota, RotaError, Week, load, save
from rotakit.schedule import plan
from rotakit.swaps import give, swap

PEOPLE = [Person("ana", "Ana", (date(2026, 11, 23),)), Person("ben", "Ben"), Person("cy", "Cy")]


def nov(day: int) -> date:
    return date(2026, 11, day)


def planned() -> Rota:
    return Rota(PEOPLE, plan(PEOPLE, nov(2), 4))


def test_plan_takes_turns_and_skips_the_away():
    assert plan(PEOPLE, nov(2), 4) == [Week(nov(2), "ana"), Week(nov(9), "ben"), Week(nov(16), "cy"), Week(nov(23), "ben")]


def test_plan_needs_a_monday():
    with pytest.raises(RotaError):
        plan(PEOPLE, nov(3), 2)


def test_plan_fails_when_everyone_is_away():
    with pytest.raises(RotaError, match="2026-11-23"):
        plan([Person("ana", "Ana", (nov(23),))], nov(16), 2)


def test_swap_exchanges_two_weeks():
    rota = planned()
    swapped = swap(rota, nov(2), nov(16))
    assert [w.person for w in swapped.weeks] == ["cy", "ben", "ana", "ben"]
    assert [w.person for w in rota.weeks] == ["ana", "ben", "cy", "ben"]


def test_swap_refuses_a_week_the_person_is_away():
    with pytest.raises(RotaError):
        swap(planned(), nov(2), nov(23))
    with pytest.raises(RotaError):
        swap(planned(), nov(2), nov(30))


def test_give_hands_a_week_over():
    assert give(planned(), nov(2), "cy").weeks[0] == Week(nov(2), "cy")
    with pytest.raises(RotaError):
        give(planned(), nov(23), "ana")
    with pytest.raises(RotaError):
        give(planned(), nov(9), "dee")


def test_ical_for_one_person():
    assert to_ical(Rota(PEOPLE, [Week(nov(2), "ana"), Week(nov(9), "ben")]), "ben") == (
        "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//rotakit//EN\r\n"
        "BEGIN:VEVENT\r\nUID:20261109-ben@rotakit\r\nDTSTART;VALUE=DATE:20261109\r\n"
        "DTEND;VALUE=DATE:20261116\r\nSUMMARY:On call: Ben\r\nEND:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )


def test_ical_for_everyone():
    text = to_ical(planned())
    assert text.count("BEGIN:VEVENT\r\n") == 4
    assert "DTEND;VALUE=DATE:20261130\r\n" in text


@pytest.fixture
def rota_file(tmp_path):
    path = tmp_path / "rota.json"
    save(Rota(PEOPLE, []), path)
    return path


def test_cli_plan_saves_and_prints(rota_file, capsys):
    assert main(["plan", str(rota_file), "--from", "2026-11-02", "--weeks", "4"]) == 0
    assert capsys.readouterr().out == "2026-11-02 Ana\n2026-11-09 Ben\n2026-11-16 Cy\n2026-11-23 Ben\n"
    assert len(load(rota_file).weeks) == 4


def test_cli_swap(rota_file, capsys):
    main(["plan", str(rota_file), "--from", "2026-11-02", "--weeks", "4"])
    capsys.readouterr()
    assert main(["swap", str(rota_file), "2026-11-02", "2026-11-16"]) == 0
    assert capsys.readouterr().out == "swapped 2026-11-02 and 2026-11-16\n"
    assert [w.person for w in load(rota_file).weeks] == ["cy", "ben", "ana", "ben"]


def test_cli_error_leaves_the_file(rota_file, capsys):
    main(["plan", str(rota_file), "--from", "2026-11-02", "--weeks", "4"])
    before = rota_file.read_bytes()
    capsys.readouterr()
    assert main(["swap", str(rota_file), "2026-11-02", "2026-11-23"]) == 1
    assert capsys.readouterr().err.startswith("rotakit: ")
    assert rota_file.read_bytes() == before


def test_cli_export_one_person(rota_file, capsys):
    main(["plan", str(rota_file), "--from", "2026-11-02", "--weeks", "4"])
    capsys.readouterr()
    assert main(["export", str(rota_file), "--person", "ben"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("BEGIN:VCALENDAR\r\n")
    assert out.count("BEGIN:VEVENT") == 2
