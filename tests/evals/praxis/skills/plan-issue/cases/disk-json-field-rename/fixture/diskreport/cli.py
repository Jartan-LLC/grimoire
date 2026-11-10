import argparse
import json
import shutil

MOUNTS = ["/"]


def usage(mount):
    total, used, _free = shutil.disk_usage(mount)
    return {"mount": mount, "used_pct": round(used * 100 / total)}


def main(argv=None):
    parser = argparse.ArgumentParser(prog="diskreport")
    parser.add_argument("--json", action="store_true", help="print JSON")
    args = parser.parse_args(argv)
    rows = [usage(m) for m in MOUNTS]
    if args.json:
        print(json.dumps(rows))
    else:
        for row in rows:
            print(f"{row['mount']:<8} {row['used_pct']}%")
