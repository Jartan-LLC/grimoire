# Rotating the signing key

1. Run `scripts/rotate-key.sh`. It makes a new key and writes its public half to `keys/`.
2. Commit `keys/`. Never commit the private key.
3. Users import the new key with `rpm --import keys/RPM-GPG-KEY-acme`.

A key that expires during a build in progress still signs that build. On macOS, gpg-agent may
cache the passphrase. rpm before 4.14 cannot read ed25519 subkeys.
