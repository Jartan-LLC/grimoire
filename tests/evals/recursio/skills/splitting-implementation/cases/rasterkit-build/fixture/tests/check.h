/* A small test harness: CHECK records a failure and carries on; main returns check_report(). */
#ifndef RASTERKIT_CHECK_H
#define RASTERKIT_CHECK_H

#include <stdio.h>

static int check_failures;

#define CHECK(condition)                                                                   \
    do {                                                                                   \
        if (!(condition)) {                                                                \
            check_failures++;                                                              \
            fprintf(stderr, "%s:%d: CHECK failed: %s\n", __FILE__, __LINE__, #condition); \
        }                                                                                  \
    } while (0)

static int check_report(const char *name) {
    if (check_failures > 0) {
        fprintf(stderr, "%s: %d failed\n", name, check_failures);
        return 1;
    }
    printf("%s: ok\n", name);
    return 0;
}

#endif
