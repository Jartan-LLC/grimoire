# The pantrykit command

Receive a lot:

```console
$ pantrykit receive pantry.json rice 12 2027-04-01
received l8: Rice x12, best-before 2027-04-01
```

Pack a household's parcel (`--dry-run` shows it without taking the stock):

```console
$ pantrykit pack pantry.json h3 2026-11-02
Rice x1 from l1
Beans x2 from l3
Oats x1 from l4
Milk x2 from l5
packed for Chen
```

See what expires in the next 30 days:

```console
$ pantrykit expiring pantry.json 2026-11-02 30
2026-11-05 l5 Milk x4
2026-11-20 l6 Milk x6
2026-12-01 l3 Beans x8
```
