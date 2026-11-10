import configparser
import pathlib

RC = pathlib.Path.home() / ".toolrc"


def load():
    parser = configparser.ConfigParser()
    parser.read(RC)
    return {s: dict(parser[s]) for s in parser.sections()}
