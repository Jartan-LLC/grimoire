"""Send a template to every row of a CSV: python3 scripts/mailer.py <csv> <template>."""
import csv
import sys
from string import Template

import sendwave


def main(csv_path, template_path):
    head, body = open(template_path).read().split("\n\n", 1)
    subject = head.removeprefix("Subject: ")
    body = Template(body)
    client = sendwave.Client.from_env()
    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            client.send(to=row["email"], subject=subject, text=body.substitute(row))
            print("sent", row["email"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
