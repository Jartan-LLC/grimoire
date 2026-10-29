"""The `rolodex` command."""

import argparse

from rolodex import store
from rolodex.models import make_contact, same_person
from rolodex.vcard import to_vcard


def main(argv: list[str] | None = None) -> None:
    """Run one subcommand."""
    parser = argparse.ArgumentParser(prog="rolodex")
    sub = parser.add_subparsers(dest="command", required=True)
    add = sub.add_parser("add")
    add.add_argument("name")
    add.add_argument("email")
    add.add_argument("--phone", default="")
    sub.add_parser("list")
    sub.add_parser("export-vcf")
    args = parser.parse_args(argv)

    contacts = store.load()
    if args.command == "add":
        new = make_contact(args.name, args.email, args.phone)
        if any(same_person(new, c) for c in contacts):
            raise SystemExit(f"already have {new['email']}")
        store.save([*contacts, new])
    elif args.command == "list":
        for c in contacts:
            print(f"{c['name']:<25} {c['email']:<30} {c['phone']}")
    elif args.command == "export-vcf":
        print("\r\n".join(to_vcard(c) for c in contacts))
