# photolib

Keeps our family photos on the NAS: every photo is a file under `library/`, and
`albums.json` lists each album's photos by path. The NAS backup keeps the last 7 days.

`python3 -m photolib list` prints every photo.
