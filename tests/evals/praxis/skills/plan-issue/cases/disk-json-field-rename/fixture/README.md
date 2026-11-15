# diskreport

`pip install diskreport`

```console
$ diskreport
/        71%
/data    38%
```

`diskreport --json` prints one object per mount:

```json
[{"mount": "/", "used_pct": 71}, {"mount": "/data", "used_pct": 38}]
```
