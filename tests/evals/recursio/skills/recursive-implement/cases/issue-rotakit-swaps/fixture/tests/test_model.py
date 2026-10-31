"""The rota's JSON file."""

from datetime import date

from rotakit.model import Person, Rota, Week, load, save


def test_save_then_load_round_trips(tmp_path):
    rota = Rota(
        [Person("ana", "Ana", (date(2026, 11, 9),)), Person("ben", "Ben")],
        [Week(date(2026, 11, 2), "ana")],
    )
    save(rota, tmp_path / "rota.json")
    assert load(tmp_path / "rota.json") == rota
