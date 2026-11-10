import sys

from photolib.scan import photos

if sys.argv[1:] == ["list"]:
    for path in photos():
        print(path)
