# envcheck

Check a `.env` file against its example.

## Usage

Run `envcheck` in the project. It lists each variable `.env.example` names that `.env` lacks, and
exits 1 when any are missing, so it can gate CI.
