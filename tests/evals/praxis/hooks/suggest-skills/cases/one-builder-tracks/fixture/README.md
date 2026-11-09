# geokit

Reads tracks of `Point`s (geokit/model.py) from three GPS formats. Each format is a module
under `geokit/formats/` with one function, `read(text: str) -> list[Point]`:

- `gpx.py`: GPX 1.1 `trkpt` elements; `lat` and `lon` attributes, `ele` and `time`
  children when present.
- `nmea.py`: `$GPGGA` sentences; degrees-minutes to decimal degrees; checksum checked,
  a bad one skipped.
- `geojson.py`: a `LineString` or a `FeatureCollection` of them; `[lon, lat, ele?]`.

Each format has its own tests in `tests/test_<format>.py`.
