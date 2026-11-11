"""Build this case's history: run by the eval runner inside the fixture repository."""

import pathlib
import subprocess

BRANCH = "feature/cli"
SUBJECT = "feat(tally): count a ballot file from the command line"
BODY = "Returning officers run the count by hand from a terminal."
FILES = {
    "tally/cli.py": '"""`python3 -m tally.cli ballots.txt`: print each candidate\'s first preferences."""\n\nimport sys\n\nfrom tally.count import first_preferences\n\n_cache = {}\n\n\ndef read_ballots(path):\n    if path in _cache:\n        return _cache[path]\n    ballots = []\n    for line in open(path).readlines():\n        ballots.append(line.strip().split(","))\n    _cache[path] = ballots\n    return ballots\n\n\ndef main():\n    try:\n        counts = first_preferences(read_ballots(sys.argv[1]))\n    except Exception:\n        pass\n    for name in counts:\n        if counts[name] == None:\n            continue\n        print(name, counts[name])\n\n\nif __name__ == "__main__":\n    main()\n'
}


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True)


git("checkout", "-q", "-b", BRANCH)
for path, text in FILES.items():
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
git("add", "-A")
git("commit", "-q", "-m", SUBJECT, "-m", BODY)
