# ratelimit

`SlidingWindow("10/m")` allows at most ten calls in any sixty seconds. Each window keeps its own count.

## Development

Run the tests with `python3 -m pytest`.
