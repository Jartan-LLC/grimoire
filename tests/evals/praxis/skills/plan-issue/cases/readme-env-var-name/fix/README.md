# podfetch

Downloads the newest episodes of the feeds listed in a file, one URL per line:

    python3 -m podfetch feeds.txt

## Settings

Three environment variables change what podfetch does:

- `PODFETCH_LIMIT`: how many of each feed's newest episodes to fetch (3 by default).
- `PODFETCH_DIR`: the folder episodes are saved under (`~/podfetch` by default), one folder
  per show.
- `PODFETCH_TIMEOUT`: seconds to wait for a feed or an episode (30 by default).

An episode whose file is already there is skipped.
