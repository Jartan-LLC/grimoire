# Pricing a stay

With these rates:

```text
first_hour = 3.00
per_hour = 2.00
daily_cap = 18.00
grace_minutes = 15
```

a car in at 08:30 and out at 10:15 stays 105 minutes: 3.00 for the first hour and 2.00 for the
second, started hour.

```console
$ parkkit fees tickets.csv rates.txt
CD34 5.00
total 5.00
```
