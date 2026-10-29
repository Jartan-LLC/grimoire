"""The `shelf` command."""

import argparse

from shelf import catalog


def main(argv: list[str] | None = None) -> None:
    """Run one subcommand."""
    parser = argparse.ArgumentParser(prog="shelf")
    sub = parser.add_subparsers(dest="command", required=True)
    add = sub.add_parser("add", help="add a book")
    add.add_argument("title")
    add.add_argument("author")
    add.add_argument("--room", default="")
    sub.add_parser("list", help="list every book")
    search = sub.add_parser("search", help="find books in the catalog by title or author")
    search.add_argument("text")
    remove = sub.add_parser("remove", help="remove a book by id")
    remove.add_argument("id", type=int)
    args = parser.parse_args(argv)

    if args.command == "add":
        print(catalog.add(args.title, args.author, args.room))
    elif args.command in ("list", "search"):
        books = catalog.load() if args.command == "list" else catalog.search(args.text)
        for book in books:
            print(f"{book['id']:>4}  {book['title']} -- {book['author']}  [{book['room']}]")
    elif args.command == "remove":
        catalog.save([b for b in catalog.load() if b["id"] != args.id])
