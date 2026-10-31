# Splitting a trip

List what everyone paid in `trip.csv`, save the day's rates in `rates.json`, then:

```console
$ tripkit balances trip.csv --home EUR --rates rates.json
ana +43.33
ben -31.67
cy -11.66
$ tripkit settle trip.csv --home EUR --rates rates.json
ben pays ana 31.67
cy pays ana 11.66
```
