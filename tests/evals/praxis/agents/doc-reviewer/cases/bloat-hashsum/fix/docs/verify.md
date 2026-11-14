# Check downloads

Run `hashsum check SHA256SUMS` in the download directory. It prints `FAILED` for each file whose
checksum does not match and exits 1 if any fail.

A checksum file with CRLF line endings is accepted. BSD-style lines, `SHA256 (file) = ...`, are
read too. A listed file that is missing is reported as `MISSING`.
