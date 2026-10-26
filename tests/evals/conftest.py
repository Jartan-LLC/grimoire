"""Keep pytest out of the eval cases: their fixtures' tests run only inside an eval sandbox."""

collect_ignore_glob = ["**/fixture/**", "**/fix/**"]
