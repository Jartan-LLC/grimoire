"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/rotate-key"
COMMITS = json.loads(
    '[{"subject": "feat(keys): add a key rotation script", "body": "", "files": {"scripts/rotate-key.sh": "#!/bin/sh\\n# Rotate the RPM signing key: make a new key, export the public half to keys/, sign with it.\\n# The private key never goes in the repository.\\nset -eu\\n"}}, {"subject": "fix(keys): keep signing a build in progress when the key expires", "body": "", "files": {"scripts/rotate-key.sh": "#!/bin/sh\\n# Rotate the RPM signing key: make a new key, export the public half to keys/, sign with it.\\n# The private key never goes in the repository.\\nset -eu\\n# A key that expires mid-build still signs that build.\\n"}}, {"subject": "fix(keys): clear gpg-agent\'s cached passphrase on macOS", "body": "", "files": {"scripts/rotate-key.sh": "#!/bin/sh\\n# Rotate the RPM signing key: make a new key, export the public half to keys/, sign with it.\\n# The private key never goes in the repository.\\nset -eu\\n# A key that expires mid-build still signs that build.\\n# macOS: gpg-agent caches the passphrase; the script reloads it.\\n"}}, {"subject": "fix(keys): make an RSA subkey for rpm before 4.14", "body": "rpm before 4.14 cannot read ed25519 subkeys.", "files": {"scripts/rotate-key.sh": "#!/bin/sh\\n# Rotate the RPM signing key: make a new key, export the public half to keys/, sign with it.\\n# The private key never goes in the repository.\\nset -eu\\n# A key that expires mid-build still signs that build.\\n# macOS: gpg-agent caches the passphrase; the script reloads it.\\n# rpm before 4.14 cannot read ed25519 subkeys, so the subkey is RSA.\\n"}}, {"subject": "docs: describe the change", "body": "", "files": {"docs/signing-key.md": "# Rotating the signing key\\n\\n1. Run `scripts/rotate-key.sh`. It makes a new key and writes its public half to `keys/`.\\n2. Commit `keys/`. Never commit the private key.\\n3. Users import the new key with `rpm --import keys/acme.asc`.\\n\\nA key that expires during a build in progress still signs that build. On macOS, gpg-agent may\\ncache the passphrase. rpm before 4.14 cannot read ed25519 subkeys.\\n"}}]'
)


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True)


git("checkout", "-q", "-b", BRANCH)
for commit in COMMITS:
    for path, text in commit["files"].items():
        target = pathlib.Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    git("add", "-A")
    git("commit", "-q", "-m", commit["subject"], "-m", commit["body"])
