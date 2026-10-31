# surveykit

Geodesy for field surveys: reads and writes coordinates in the formats our crews use, converts to
and from UTM, measures distances and bearings on the WGS84 ellipsoid, works out plot areas, and
summarises GPS tracks. A library and a command.

## Data model

`src/surveykit/model.py` holds `LatLon` (decimal degrees), `Ellipsoid` with the `WGS84` constants,
`TrackPoint` (time, position and elevation), `Polygon` (an unclosed ring of `LatLon`s),
`GeodesyError` and `MEAN_EARTH_RADIUS_M`. Every module below works on these and on nothing else from
its siblings; only the command uses them all. A module that needs a spherical distance computes it
itself with `MEAN_EARTH_RADIUS_M`.

Throughout, longitudes are normalised to the range -180 (included) to 180 (excluded) and bearings
to 0 (included) to 360 (excluded), in degrees clockwise from true north.

## Coordinates (`surveykit.coords`)

- `parse_coordinate(text) -> LatLon` reads a latitude and a longitude, in that order, separated by
  a comma or by whitespace, in any of these forms, upper or lower case:
  - decimal degrees, signed or with a hemisphere letter before or after: `52.2053, 0.1218`,
    `52.2053 N 0.1218 E`, `S 33.8688 E 151.2093`;
  - degrees, minutes and seconds, with spaces or with `d`, `'` and `"` as separators:
    `52 12 19.08 N, 0 07 18.48 E`, `52d12'19.08"N 0d07'18.48"E`;
  - degrees and decimal minutes: `N 52 12.318, E 0 07.308`.

  A hemisphere letter and a minus sign together, minutes or seconds of 60 or more, a latitude
  outside -90..90, a longitude outside -180..180, or a latitude letter on the longitude raise
  `GeodesyError` naming the problem.
- `format_latlon(p, style="decimal", precision=None) -> str`:
  - `decimal`: signed, six places by default: `52.205300, 0.121800`;
  - `dms`: `52 12 19.08 N, 0 07 18.48 E`, seconds to two places by default, minutes and seconds
    zero-padded to two digits; rounding carries, so 59.996 seconds becomes the next minute;
  - `ddm`: `52 12.3180 N, 0 07.3080 E`, minutes to four places by default.
- `to_utm(p, ellipsoid=WGS84) -> Utm` and `from_utm(utm, ellipsoid=WGS84) -> LatLon`. `Utm` holds
  `zone` (1 to 60), `band` (a letter), `hemisphere` (`N` or `S`), `easting` and `northing` in
  metres. Use the Krueger series in the third flattening to order n^6 (Karney 2011), with scale
  factor 0.9996, false easting 500000 m, and false northing 10000000 m in the south. `to_utm`
  then `from_utm` returns the start point to within 1e-9 degrees anywhere in a zone.
- Zones are 6 degrees wide from 180 W, so zone 31 runs from 0 to 6 E, with two exceptions: from
  56 N to 64 N, longitudes 3 to 12 E are zone 32; from 72 N to 84 N, zones 32, 34 and 36 do not
  exist, and longitudes 0 to 9 E are zone 31, 9 to 21 E zone 33, 21 to 33 E zone 35 and 33 to 42 E
  zone 37. Each lower bound is included and each upper bound excluded.
- Latitude bands are the letters `C` to `X` without `I` and `O`, 8 degrees each from 80 S, except
  `X`, which covers 72 N to 84 N. A latitude outside 80 S to 84 N raises `GeodesyError`.
- The equator at 3 E is `31N 500000 0`.
- `format_utm(utm) -> str` writes `31U 448252 5411932`, zone, band, then easting and northing
  rounded to whole metres. `parse_utm(text)` reads that form; the band sets the hemisphere (`N` and
  later letters are north). `from_utm` raises `GeodesyError` when the easting is outside 100000 to
  900000 m.

## Geodesics (`surveykit.geodesic`)

- `vincenty_inverse(p1, p2, ellipsoid=WGS84) -> Inverse` holds `distance_m`, `initial_bearing` and
  `final_bearing`. Iterate on the longitude difference until it changes by less than 1e-12 radians;
  after 200 iterations without converging, which happens for nearly antipodal points, raise
  `GeodesyError("vincenty did not converge")`. Equal points give a distance of 0 and bearings of 0.
  Points on the equator need the cos^2(alpha) = 0 case. Vincenty's own example, Flinders Peak
  (37 57 03.72030 S, 144 25 29.52440 E) to Buninyong (37 39 10.15610 S, 143 55 35.38390 E), gives
  54972.271 m, an initial bearing of 306 52 05.37 and a final bearing of 307 10 25.07.
- `vincenty_direct(p, bearing, distance_m, ellipsoid=WGS84) -> tuple[LatLon, float]`: the point
  reached and the final bearing, iterating on sigma to the same 1e-12 tolerance. Direct then
  inverse returns the distance to within 1 mm.
- On the sphere of radius `MEAN_EARTH_RADIUS_M`: `haversine_m(p1, p2)` (one degree of longitude
  on the equator is 111195.080 m), `initial_bearing(p1, p2)`, `final_bearing(p1, p2)` (the
  initial bearing from `p2` to `p1` plus 180), `midpoint(p1, p2)`, `destination(p, bearing,
  distance_m)` and `cross_track_m(p, start, end)`, the signed distance from `p` to the great
  circle through `start` and `end`, negative to the left of the direction of travel.

## Polygons (`surveykit.polygons`)

- `area_m2(polygon, radius=MEAN_EARTH_RADIUS_M) -> float`: the spherical excess E summed over the
  edges as 2 atan2(tan(dlon / 2) (tan(phi1 / 2) + tan(phi2 / 2)), 1 + tan(phi1 / 2) tan(phi2 / 2)),
  with dlon wrapped to -pi..pi, and the area |E| R^2. When |E| is more than 2 pi the ring is read
  as enclosing the smaller region and the area is (4 pi - |E|) R^2. Fewer than three vertices raise
  `GeodesyError`.
- `perimeter_m(polygon)`: the sum of the haversine edge lengths, closing edge included.
- `is_clockwise(polygon) -> bool`: the sign of E.
- `contains(polygon, point) -> bool`: ray casting on longitude and latitude, after unwrapping
  every longitude, the point's included, to within 180 degrees of the first vertex, so a polygon
  that crosses the antimeridian, such as one with vertices at 179 E and 179 W, works. A point on an
  edge or a vertex is inside.
- `bounding_box(polygon) -> tuple[float, float, float, float]`: south, west, north and east. For a
  polygon that crosses the antimeridian, west is greater than east.
- `simplify(points, tolerance_m) -> list[LatLon]`: Douglas-Peucker on an open line. The distance
  of a point to a segment is its cross-track distance when its along-track position falls between
  the segment's ends, and otherwise its haversine distance to the nearer end. The first and last
  points are always kept, and so is any point farther than `tolerance_m` from the segment between
  the points kept around it. It must work on 100000 points, so no recursion. A negative tolerance
  raises `GeodesyError`.
- `simplify_polygon(polygon, tolerance_m) -> Polygon` simplifies the ring as a line from its first
  vertex back to it, and never returns fewer than three vertices.

## GPS tracks (`surveykit.tracks`)

- `read_gpx(text) -> list[TrackPoint]` reads every `trkpt` of every `trkseg` of a GPX 1.0 or 1.1
  file (attributes `lat` and `lon`, children `ele` and `time` in ISO 8601 with `Z` or an offset),
  whatever the XML namespace. A point without a time raises `GeodesyError` naming its index.
- `read_csv(text) -> list[TrackPoint]` reads a header row with the columns `time`, `lat`, `lon` and
  optionally `ele`, in any order.
- `summarize(points, moving_speed_ms=0.5) -> TrackSummary` with `distance_m`, `moving_distance_m`,
  `elapsed_s`, `moving_s`, `gain_m`, `loss_m`, `max_speed_ms` and `splits`. Distances are
  haversine distances between consecutive points.
- Points must be in time order: a point earlier than the one before raises `GeodesyError`, and a
  point with the same time as the one before is dropped.
- A segment is moving when its speed is at least `moving_speed_ms`; moving distance and time sum
  those segments.
- Elevation gain and loss use 3 m hysteresis: keep a reference elevation, starting at the first
  known one; when a point is 3 m or more above it, add the difference to the gain and move the
  reference there, and likewise for the loss below it. Points with no elevation are skipped.
- A spike is a single point, neither first nor last, whose segments in and out both have a speed
  over the larger of 5 m/s and three times the median segment speed, while the segment from the
  point before it to the point after it does not. Spikes are dropped before anything else is
  computed. `max_speed_ms` is then the fastest segment.
- `splits` holds one `Split(km, duration_s, distance_m)` per kilometre, the time each kilometre
  mark is passed being interpolated linearly within its segment; a final partial split carries its
  own distance. A track of fewer than two points has zero for everything and no splits.

## Command (`surveykit.cli`)

- `surveykit dist FILE` reads one pair of coordinates per line, `FROM ; TO`, each in any form
  `parse_coordinate` takes, and prints per line the Vincenty distance in km to three places, the
  initial and final bearings to one place, and the haversine distance:
  `54.972 km  306.9 -> 307.2  (sphere 54.926 km)`. A pair that does not converge prints
  `no convergence` and the rest carry on.
- `surveykit area FILE [--simplify METRES]` reads one vertex per line and prints the area in m^2
  and ha, the perimeter in m, and the bounding box.
- `surveykit track FILE [--moving-speed M/S] [--splits]` reads a `.gpx` or `.csv` track and prints
  the summary, times as `H:MM:SS`, and with `--splits` one line per kilometre.
- `surveykit utm COORD` prints the UTM form of one coordinate, and `surveykit utm --inverse UTM`
  prints the decimal form of a UTM position.

A line that does not parse prints to stderr as `FILE:LINE: message` and is skipped, and the command
ends with status 1. A file that cannot be read, or a track in another format, exits 2.

## Status

Only the data model exists.
