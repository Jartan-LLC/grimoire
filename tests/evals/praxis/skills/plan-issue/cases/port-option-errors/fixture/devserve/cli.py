import argparse
import functools
import http.server


def parse(argv):
    parser = argparse.ArgumentParser(prog="devserve")
    parser.add_argument("--dir", default=".", help="folder to serve")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse(argv)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=args.dir)
    http.server.ThreadingHTTPServer(("127.0.0.1", 8000), handler).serve_forever()
