# pathglob

Matches slash-separated paths against glob patterns, the way `.gitignore`-style tools do, with
no dependency on the file system: `match("src/**/*.py", "src/app/models/user.py")` is true.
