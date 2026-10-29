import pytest

from rolodex.cli import main


@pytest.fixture(autouse=True)
def contacts_file(tmp_path, monkeypatch):
    monkeypatch.setenv("ROLODEX_FILE", str(tmp_path / "contacts.json"))


def test_add_and_list(capsys):
    main(["add", "Ada Lovelace", "Ada@Example.com"])
    main(["list"])
    assert "ada@example.com" in capsys.readouterr().out


def test_refuses_a_duplicate_email():
    main(["add", "Ada", "ada@example.com"])
    with pytest.raises(SystemExit, match="already have"):
        main(["add", "Ada L.", "ADA@example.com"])
