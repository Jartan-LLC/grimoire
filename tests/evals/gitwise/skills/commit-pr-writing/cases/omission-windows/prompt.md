`paths.normalize` should collapse repeated slashes (`a//b` -> `a/b`). Make that change with a test and
commit. Leave Windows-style backslash paths alone on purpose: nobody here can test on Windows, and a
wrong guess would break the one user who runs it there.
