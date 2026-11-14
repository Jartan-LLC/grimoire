"""Print release notes for main since the last tag, grouped by commit type."""
import subprocess

SECTIONS = {"feat": "Features", "fix": "Fixes"}


def subjects():
    tag = subprocess.run(["git", "describe", "--tags", "--abbrev=0"],
                         capture_output=True, text=True, check=True).stdout.strip()
    log = subprocess.run(["git", "log", "--first-parent", "--format=%s", f"{tag}..main"],
                         capture_output=True, text=True, check=True).stdout
    return log.splitlines()


def main():
    groups = {name: [] for name in SECTIONS.values()}
    for subject in subjects():
        kind, _, text = subject.partition(": ")
        kind = kind.split("(")[0]
        if kind in SECTIONS:
            groups[SECTIONS[kind]].append(text)
    for title, items in groups.items():
        if items:
            print(f"## {title}")
            print("\n".join(f"- {i}" for i in items))


if __name__ == "__main__":
    main()
