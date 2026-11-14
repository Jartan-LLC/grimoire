# dots

Put your dotfiles in `~/dotfiles` (or `$DOTS_DIR`), then on each machine:

```bash
dots list      # the dotfiles dots manages
dots link      # symlink each one into your home directory
dots status    # which links are missing or point elsewhere
```

Most setup scripts end with `dots link`.
