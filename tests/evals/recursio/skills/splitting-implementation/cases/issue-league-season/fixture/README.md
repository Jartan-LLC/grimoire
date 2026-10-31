# leaguekit

Runs a league season: draws up the fixture schedule, keeps the table, rates the teams, and plays
out the end-of-season playoffs, as a library and a command.

## Data model

`src/leaguekit/model.py` holds the records the modules pass to one another: `Team`, `Match` (a
fixture, with its `Result` once played), `StandingRow` (one line of a table), the `TiebreakRule`
enum with `DEFAULT_TIEBREAKERS`, and `LeagueError`. Every module below works on these and nothing
else of its siblings, except the command, which uses them all. Bad input raises `LeagueError` with
a message naming the team, round or value at fault.

## Schedule (`leaguekit.schedule`)

- `round_robin(codes, legs=1)` returns the rounds of a round robin, each a list of
  `(home, away)` pairs. `legs` is 1 or 2; fewer than two teams or a repeated code is an error.
  The pairings come from the circle method:
  1. Let `p` be the codes in the order given. With an odd count, put a bye (`None`) in front, so
     the bye is the fixed entry. Let `n` be the length of `p`; there are `n - 1` rounds.
  2. In round `r` (counting from 0), pair `p[i]` with `p[n - 1 - i]` for `i` from 0 to
     `n / 2 - 1`, listed in that order.
  3. Pair 0: `p[0]` is at home in even rounds and away in odd rounds. Pair `i >= 1`: `p[i]` is
     at home when `i` is odd, otherwise `p[n - 1 - i]` is.
  4. After each round, keep `p[0]` and rotate the rest one place to the right:
     `[p[0], p[n - 1], p[1], ..., p[n - 2]]`.
  5. A pair holding the bye is left out of the round; that team rests.

  For `ANT BEE CAT DOG` the rounds are `ANT-DOG BEE-CAT`, then `CAT-ANT DOG-BEE`, then
  `ANT-BEE CAT-DOG`. With `legs=2` the second half repeats the first half's rounds in the same
  order with home and away swapped.
- `breaks(rounds)` counts each team's breaks: two consecutive rounds both at home or both away.
  A round the team rests ends a run. The orientation above gives exactly `n - 2` breaks over a
  single round robin with an even count, no team more than one, and none with an odd count.
- `round_dates(count, start, blackouts=())` dates `count` rounds: round 1 on `start`, each
  later round 7 days after the one before. A round whose date is in `blackouts` moves 7 days
  later, again as often as needed, and the rounds after it count from the moved date. With
  `start` 2026-08-08 and a blackout on 2026-08-22, four rounds fall on 08-08, 08-15, 08-29 and
  09-05.
- `build_schedule(teams, start, legs=1, blackouts=())` returns the `Match`es of the season,
  rounds numbered from 1, dated by `round_dates`, unplayed, ordered by round and then as
  `round_robin` lists them. Teams enter the circle in seed order.

## Standings (`leaguekit.standings`)

`table(teams, matches, points=(3, 1, 0), shootout=None, tiebreakers=DEFAULT_TIEBREAKERS, fair_play=None)`
returns one `StandingRow` per team, in table order. Only matches with a result count; a match naming a team not in `teams` is an error.

- **Points**: `points` gives the points for a win, a draw and a loss. Goals include extra time.
  `shootout`, when given as `(winner, loser)`, replaces the draw points of a drawn match that
  went to a shoot-out (a league that settles draws on penalties); without it, a shoot-out is
  ignored. A match with a shoot-out counts in the drawn column either way.
- **Tiebreakers**: the rules apply in order, each to the teams level on every rule before it.
  - `POINTS`: more points first.
  - `HEAD_TO_HEAD`: for a group of two or more teams level so far, build a mini table from the
    played matches among exactly those teams, with the same points rules, and rank by mini-table
    points, then mini-table goal difference, then mini-table goals scored. If that tells the
    group apart only in part, each smaller group still level goes through `HEAD_TO_HEAD` again,
    with a mini table recomputed from its own matches only, until nothing changes; only then do
    the teams still level move on to the next rule. A group with no played matches among its
    teams stays level.
  - `GOAL_DIFFERENCE`, `GOALS_FOR` and `AWAY_GOALS` (goals scored in away matches): the
    whole-season totals, higher first.
  - `FAIR_PLAY`: fair-play points from the `fair_play` mapping of code to points (1 per caution
    and 3 per sending-off, kept by the league office), lower first; a team not in the mapping
    has 0.
  - `LOT`: seed, lower first. It always tells teams apart, since seeds are unique.

  Teams still level after the last rule share a position and are listed by code; the next
  position skips, as in 1, 2, 2, 4.
- `form(code, matches, last=5)` returns the team's last `last` played matches as a string of
  `W`, `D` and `L`, oldest first, ordered by round and then list order. A shoot-out is a `D`.

## Ratings (`leaguekit.ratings`)

Elo ratings in the style of the World Football Elo Ratings.

- `expected_score(rating, opponent)` is `1 / (1 + 10 ** ((opponent - rating) / 400))`.
- `margin_multiplier(goal_difference)` takes the absolute goal difference: 1 for 0 or 1, 1.5 for
  2, and `(11 + n) / 8` for `n` of 3 or more.
- `update(home, away, result, importance="league", neutral=False)` returns the two new
  ratings. K is 20 for `"friendly"`, 30 for `"league"`, 40 for `"playoff"` and 50 for
  `"final"`; any other importance is an error. The home side's expected score is worked out with
  65 points of home advantage added to its rating, unless `neutral`. The actual score is 1 for a
  win, 0.5 for a draw and 0 for a loss, on goals including extra time; a shoot-out counts as a
  draw and its goals are ignored. The home side gains `K x G x (W - We)`, where G is the margin
  multiplier, and the away side loses the same. Example: two 1500 teams, a league match, home
  wins 2-0: We = 0.5925, G = 1.5, so the ratings become 1518.3 and 1481.7.
- `rate(teams, matches, importance=None)` runs a season from each team's `rating`. Played
  matches are taken in round order, then list order; unplayed ones are skipped. `importance`
  maps a round number to its importance, `"league"` for a round not in it. It returns a
  `RatingRun` (defined in this module): `ratings`, a dict of code to final rating, and
  `changes`, one `RatingChange(match, home_before, away_before, change)` per rated match.
- `regress(ratings, factor=1/3, mean=None)` moves each rating toward the mean between seasons:
  `r + (m - r) x factor`, where `m` is `mean` or, when None, the mean of the given ratings. A
  factor outside 0 to 1 is an error.

## Playoffs (`leaguekit.playoffs`)

- `seed_order(size)` gives the bracket positions by seed for a power-of-two `size`: start from
  `[1]` and, until the list has `size` entries, replace each seed `s` with `s, 2k + 1 - s`, where
  `k` is the current length. Size 8 gives `1 8 4 5 2 7 3 6`, so seeds 1 and 2 can meet only in
  the final. Any other size is an error.
- `first_round(codes)` takes the qualified teams best first and pairs them by `seed_order` for
  the smallest power of two that holds them all. A seed beyond the count is a bye: the team
  facing it goes through without a match, so the top seeds get the byes. Six teams give
  `1 v bye, 4 v 5, 2 v bye, 3 v 6`. Fewer than two teams is an error.
- `decide(first, second, matches, away_goals=False)` returns the winner of a tie between the
  codes `first` and `second` from its played matches, in round order. One match: more goals
  wins, extra time included, then the shoot-out. Two legs: the aggregate of each team's goals
  over both legs; if level and `away_goals` is set, more goals scored away from home wins, extra
  time in the second leg counting as away goals for the visitors; if still level, the second
  leg's shoot-out decides. A tie that ends level with no shoot-out is an error, and so is a
  match between other teams.
- `run_bracket(codes, matches, two_legs=False, away_goals=False, third_place=True)` plays the
  bracket out as far as `matches` allow and returns a `Bracket` (defined in this module): its
  rounds, each a name and a list of ties, each tie its two codes, its matches and its winner, or
  None when undecided. The higher seed plays the second leg at home. The final and the
  third-place match are always one match, at a neutral ground listed with the higher seed as
  home. Round names follow the number of teams in the round: `Final` for 2, `Semi-finals` for
  4, `Quarter-finals` for 8, otherwise `Round of N`; the third-place match, between the losing
  semi-finalists, comes before the final as `Third place`. A tie whose teams are not yet known
  shows `?` for each missing team.
- `render(bracket)` returns a text bracket: each round's name, then one line per tie, indented
  two spaces: `ANT: bye` for a bye, `?` for an unknown team, otherwise
  `first v second: legs -> winner`. Each leg is its score from `first`'s side, followed by a space
  and `aet` after extra time and by a space and `pens 4-3` after a shoot-out; legs are joined by a
  comma and a space, and two legs end with a space and `(agg 3-2)`. An undecided tie ends `-> ?`. Example:
  `BEE v GNU: 0-1, 3-1 aet -> BEE (agg 3-2)`.

## Command (`leaguekit.cli`)

Files are CSV with a header row:

- teams: `code,name,seed,rating`; an empty rating is 1500.
- matches: `round,date,home,away,score`. `date` is ISO 8601 or empty. `score` is empty for an
  unplayed match, or `H-A`, then optionally `aet`, then optionally `pens H-A`, separated by single
  spaces: `2-1`, `1-1 aet`, `2-2 aet pens 4-3`.
- fair play: `code,points`.

Subcommands:

- `leaguekit schedule TEAMS --start DATE [--double] [--blackout DATE]...` prints the season's
  matches as a matches CSV, scores empty, and `N rounds, M matches, B breaks` on stderr.
- `leaguekit table TEAMS MATCHES [--points W,D,L] [--shootout W,L] [--tiebreak RULE,...] [--fair-play FILE]`
  prints the table: columns Pos, Team, P, W, D, L, GF, GA, GD, Pts and Form,
  right-aligned except Team and Form, GD signed (`+3`, `0`, `-2`). `--tiebreak` takes the
  `TiebreakRule` values, as `points,head-to-head,lot`.
- `leaguekit ratings TEAMS MATCHES [--importance ROUND=KIND]... [--regress FACTOR]` prints
  rank, team, final rating and its change over the season, one decimal place, the change signed;
  with `--regress`, a last column holds next season's starting rating.
- `leaguekit bracket TEAMS MATCHES --top N [--playoffs FILE] [--two-legs] [--away-goals] [--no-third-place]`
  seeds the top `N` of the table, worked out with the default rules, and
  prints the rendered bracket, played out from the playoff matches in `--playoffs`.

A bad row prints `FILE:LINE: message` on stderr, numbered from 1 with the header as line 1, and is
skipped. The exit status is 0, or 1 when any row was skipped, or 2 when a file cannot be read, an
option is bad or the tools raise `LeagueError`, which prints as `leaguekit: message`.

## Status

Only the data model exists.
