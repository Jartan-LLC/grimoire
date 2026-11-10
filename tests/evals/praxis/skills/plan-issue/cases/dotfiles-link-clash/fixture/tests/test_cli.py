from pathlib import Path

from dots.cli import main


def test_link_makes_symlinks(tmp_path, monkeypatch, capsys):
    (tmp_path / "dotfiles").mkdir()
    (tmp_path / "dotfiles" / ".vimrc").write_text("set number\n")
    monkeypatch.setenv("DOTS_DIR", str(tmp_path / "dotfiles"))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    main(["link"])
    assert (tmp_path / ".vimrc").is_symlink()
    assert capsys.readouterr().out.splitlines()[-1] == "linked 1 dotfiles"
