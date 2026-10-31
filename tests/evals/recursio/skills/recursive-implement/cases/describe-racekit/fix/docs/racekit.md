# Using racekit

Every finisher's place, then the runners who did not finish:

```console
$ racekit results results.csv 2026
1 9 Gus Hale 0:36:44 MSEN
2 7 Ben Ola 0:38:30 MU20
3 22 Fay Lund 0:40:25 FV35
4 12 Ana Ruiz 0:41:07 FV35
5 31 Cy Park 0:44:48 MV50
6 4 Dee Moss 0:46:45 FSEN
DNF 19 Eli Shah
```

One category's places, with `--category`:

```console
$ racekit results results.csv 2026 --category FV35
1 22 Fay Lund 0:40:25 FV35
2 12 Ana Ruiz 0:41:07 FV35
```

The winner of each category:

```console
$ racekit winners results.csv 2026
FSEN 4 Dee Moss 0:46:45
FV35 22 Fay Lund 0:40:25
MU20 7 Ben Ola 0:38:30
MSEN 9 Gus Hale 0:36:44
MV50 31 Cy Park 0:44:48
```
