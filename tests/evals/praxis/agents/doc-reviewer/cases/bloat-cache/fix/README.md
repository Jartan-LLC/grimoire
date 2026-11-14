# fetchy

Download files with retries.

## Usage

`fetchy URL` downloads `URL` into the current directory.

`--cache-dir DIR` keeps downloads in `DIR` and serves a repeat request from it.

On NFS, where flock does nothing, a lock file is used. Paths past Windows' 260-character MAX_PATH
are hashed. An entry stamped by a clock running ahead is fetched again.
