CC ?= cc
CFLAGS ?= -std=c11 -Wall -Wextra -O2
LDLIBS = -lm

LIB_OBJ := $(patsubst src/%.c,build/%.o,$(filter-out src/cli.c,$(wildcard src/*.c)))
TESTS := $(patsubst tests/%.c,build/%,$(wildcard tests/test_*.c))
HEADERS := $(wildcard src/*.h)

.PHONY: all test clean

all: build/librasterkit.a $(TESTS) $(if $(wildcard src/cli.c),build/rasterkit)

build:
	mkdir -p build

build/%.o: src/%.c $(HEADERS) | build
	$(CC) $(CFLAGS) -Isrc -c $< -o $@

build/librasterkit.a: $(LIB_OBJ)
	ar rcs $@ $^

build/test_%: tests/test_%.c tests/check.h build/librasterkit.a $(HEADERS)
	$(CC) $(CFLAGS) -Isrc $< build/librasterkit.a $(LDLIBS) -o $@

build/rasterkit: src/cli.c build/librasterkit.a $(HEADERS)
	$(CC) $(CFLAGS) -Isrc $< build/librasterkit.a $(LDLIBS) -o $@

test: $(TESTS)
	@set -e; for t in $(TESTS); do ./$$t; done

clean:
	rm -rf build
