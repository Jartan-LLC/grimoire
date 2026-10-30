# tunekit

Turns folk tunes written in ABC notation into Standard MIDI Files, transposes them, names their
chords and describes them, as a library and a command. No npm dependencies.

## Contract

`src/types.js` holds what the modules pass to one another: `Note`, `Tune`, `Meter`, `KeySignature`
and `Mode` (JSDoc typedefs), `TuneError`, and the constants `TICKS_PER_QUARTER` (480),
`DEFAULT_VELOCITY` (80), `MODES`, `MAJOR_KEY_FIFTHS`, `MODE_FIFTHS_OFFSET` and `SHARP_ORDER`.
Pitches are MIDI note numbers with C4 = 60; times are ticks. Each module below uses only these and
nothing of its siblings; only the command uses them all.

## ABC reader (`src/abc.js`)

`parseAbc(text)` returns every tune in the file as a `Tune[]`; a tune starts at an `X:` line and
runs to the next blank line or the end. Text before the first `X:` is ignored. `parseTune(text)`
returns the first tune. Bad input throws `TuneError` with the line and column (both from 1).

Header: lines of the form `F:value`, from `X:` to `K:`, which ends the header. `%` starts a
comment to the end of the line, in the header and the body.

- `X:` the index, an integer. `T:` the title; a later `T:` line is ignored.
- `M:` the meter: `6/8`, `C` for 4/4, `C|` for 2/2. Default 4/4.
- `L:` the unit length, as `1/8`. Default, from ABC 2.1: 1/16 when the meter as a fraction is
  below 0.75 (2/4 is 0.5), otherwise 1/8.
- `Q:` the tempo as `1/4=120` or `3/8=80`, converted to quarter notes per minute (`3/8=80` is
  120). Default 120.
- `K:` the key: a tonic letter, an optional `#` or `b`, then an optional mode: `G`, `Em`, `Ador`,
  `F#mix`, `Bbmin`, `E phrygian`. Modes match on their first three letters, case-insensitive;
  `m` alone is minor; no mode is major. The signature is `MAJOR_KEY_FIFTHS[tonic] +
  MODE_FIFTHS_OFFSET[mode]`; a key outside -7 to 7 (`G#` major) is a `TuneError`.
- Every other field (`C:`, `R:`, `S:`, `N:`, `Z:`, `w:`) is ignored. A tune with no `K:` line is a
  `TuneError`.

Body, after `K:`:

- Notes: `C D E F G A B` are C4 to B4 (C = 60); `c` to `b` are an octave higher (c = 72). Each `'`
  after the letter raises an octave, each `,` lowers one: `C,` is 48, `c'` is 84.
- Accidentals before the letter: `^` sharp, `^^` double sharp, `_` flat, `__` double flat, `=`
  natural. A note without one takes the key signature (in G, `F` is 66). An accidental carries to
  later notes of the same letter and octave until the next bar line.
- Lengths after the note multiply the unit length: `2`, `3`, `3/2`, `/` (a half), `//` (a
  quarter), `/4`, `3/`. A note's ticks are `num / den x 4 x TICKS_PER_QUARTER x multiplier`: with
  `L:1/8`, `A` is 240 ticks and `A3/2` is 360. A zero denominator is a `TuneError`.
- Rests: `z` and `x` take lengths like notes and advance time without making a `Note`.
- Chords: `[CEG]` starts its notes together. A length after `]` multiplies every note in it; time
  moves on by the length of the chord's first note. An unclosed `[` is a `TuneError`.
- Ties: `-` after a note joins it to the next note of the same pitch, across a bar line too, as one
  `Note` with the summed duration. A tie to a different pitch is dropped.
- Broken rhythm: `A>B` makes A 3/2 and B 1/2 of their lengths; `A<B` the reverse; `>>` gives 7/4
  and 1/4, `>>>` 15/8 and 1/8.
- Tuplets: `(3abc` plays three notes in the time of two, `(2` two in the time of three, `(4` four
  in the time of three, and `(p:q:r` p notes in the time of q for the next r notes. With `L:1/8`,
  each note of `(3abc` is 160 ticks.
- Bar lines: `|`, `||`, `[|`, `|]`, `|:`, `:|`, `::`. Repeats are unrolled into playing order:
  `|: A B :|` gives A B A B. A `:|` with no `|:` repeats from the start of the tune or the last
  `||`. `::` ends one repeat and starts the next.
- Endings: `[1` or `|1` starts the first ending, `[2` or `:|2` the second; the first is played the
  first time through, the second the second time.
- Ignored: spaces (beaming only), decorations (`~`, `.`, `H`, `L`, `M`, `O`, `P`, `S`, `T`, `u`,
  `v` and `!trill!` style), chord symbols and annotations in double quotes, grace notes in `{...}`.
  Any other character is a `TuneError`.

Velocity: a note starting on the first beat of a bar gets 100, every other note
`DEFAULT_VELOCITY`. `Tune.notes` is sorted by start, then pitch.

## Theory (`src/theory.js`)

- `parseNoteName(name)`: `"F#4"` to 66; accepts `#`, `##`, `b` and `bb`. The octave belongs to the
  letter, so `"Cb4"` is 59 and `"B#3"` is 60. Anything else throws `RangeError`.
- `keySignature(key)`: `{ fifths, sharps, flats }`, the letters in `SHARP_ORDER` (sharps) or its
  reverse (flats): A dorian is `{ fifths: 1, sharps: ["F"], flats: [] }`.
- `scale(tonic, mode)`: the seven note names, one per letter, no octave: D dorian is
  `D E F G A B C`, Bb major is `Bb C D Eb F G A`, F# major ends with `E#`.
- `spell(pitch, key)`: the name with octave. A pitch in the key's scale takes the scale's
  spelling; any other pitch is spelled with a sharp in keys with sharps or none, and with a flat in
  keys with flats. 66 is `F#4` in C major and `Gb4` in F major; 59 is `Cb4` in Gb major.
- `transposeKey(key, semitones)`: the tonic moves by the interval and is respelled to the key of
  the same mode with the fewest accidentals: D major + 1 is Eb major, not D# major. At 6 sharps
  against 6 flats, sharps win (F# major, D# minor).
- `transposeTune(tune, semitones)`: a new `Tune` with every pitch moved and the key from
  `transposeKey`; the original is untouched. A pitch leaving 0-127 throws `RangeError`.
- `nameChord(pitches, key = C major)`: the chord name for a set of MIDI pitches, or `null`.
  Doubled pitch classes count once; fewer than three pitch classes is `null`. Every pitch class is
  tried as the root against these interval sets, in this order: `maj` {0, 4, 7}, `min` {0, 3, 7},
  `dim` {0, 3, 6}, `aug` {0, 4, 8}, `7` {0, 4, 7, 10}, `maj7` {0, 4, 7, 11}, `m7` {0, 3, 7, 10},
  `sus2` {0, 2, 7}, `sus4` {0, 5, 7}. The suffixes are `""`, `m`, `dim`, `aug`, `7`, `maj7`,
  `m7`, `sus2` and `sus4`. When more than one reading matches (`aug` always does; Csus2 has the
  pitches of Gsus4), the one whose root is the lowest pitch wins, then the earlier in the list.
  When the lowest pitch is not the root, `/` and the bass are appended: [64, 67, 72] is `C/E`.
  Names are spelled with `spell` in `key`, without octave.

## MIDI (`src/midi.js`)

`writeMidi(tune, { format = 1, channel = 0, program = 0 })` returns a `Uint8Array`.

- Header chunk: `MThd`, length 6, then format, track count and division (480), each 16-bit big
  endian. Chunk lengths are 32-bit big endian.
- Format 0 is one `MTrk` with everything. Format 1 has a conductor track (track name, time
  signature, key signature, tempo, end of track) and a note track (program change at tick 0, notes,
  end of track).
- Meta events: track name `FF 03 len text` (the title); tempo `FF 51 03` and microseconds per
  quarter as 24 bits, `round(60000000 / tempo)`, 500000 at 120; time signature `FF 58 04 nn dd 18
  08` with the denominator as a power of two (8 is 3); key signature `FF 59 02 sf mi`, sf the
  signed fifths as one byte (-2 is `FE`), mi 1 for minor or aeolian and 0 for every other mode;
  end of track `FF 2F 00`.
- Notes: note on `9n pitch velocity`, note off `8n pitch 40` (velocity 64), n the channel. At the
  same tick, note-off events come before note-on events, then ascending pitch. No running status.
- Delta times are variable-length quantities, 7 bits a byte, high bit set on every byte but the
  last: 0 is `00`, 127 is `7F`, 128 is `81 00`, 480 is `83 60`, 0x0FFFFFFF is `FF FF FF 7F`.
  Anything larger throws `RangeError`.

`readMidi(bytes)` returns `{ format, division, tracks }`, each track a list of events with their
absolute tick. `midiToTune(bytes)` builds a `Tune` from it:

- Reads formats 0 and 1 and accepts running status. A note on pairs with the next note off, or
  note on with velocity 0, of the same pitch and channel, first in first out.
- Sysex events (`F0` and `F7` with a variable-length size) and unknown meta events are skipped,
  and so are chunks of an unknown type, by their length.
- A division other than 480 is rescaled to 480 ticks, rounded. A division with the high bit set
  (SMPTE time) is a `TuneError`, and so are a wrong chunk id and data that ends early; the message
  gives the byte offset.
- Title from the first track name (empty when none), tempo from the first tempo event (default
  120, rounded to a whole number), meter from the first time signature (default 4/4), key from the
  first key signature (default C major; sf 0 mi 1 is A minor), unit length [1, 8], index 1.

Round trip: `midiToTune(writeMidi(tune))` has the same notes, tempo, meter, key and title, for
either format.

## Analysis (`src/analysis.js`)

- `range(tune)`: `{ lowest, highest, semitones }` as MIDI numbers, or `null` with no notes.
- `intervalHistogram(tune)`: the melody is the highest note of each start time; returns
  `[interval, count]` pairs for the signed semitone steps between consecutive melody notes, sorted
  by interval.
- `densityByBar(tune)`: one number per bar, the note onsets in the bar per quarter note, rounded to
  two decimals. A bar is `beats x 4 / unit x TICKS_PER_QUARTER` ticks (1440 in 6/8), counted from
  tick 0. A chord is one onset. Bars run to the bar holding the last note's start; an empty bar
  inside is 0.
- `estimateKey(tune)`: the Krumhansl-Schmuckler estimate. Sum the duration in ticks of each pitch
  class, then take the Pearson correlation of that profile with each of the 24 keys' profiles
  (the profile below rotated to the tonic). Major: 6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19,
  2.39, 3.66, 2.29, 2.88. Minor: 6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34,
  3.17. Returns `{ key, correlation, ranking }`, `ranking` the best three as
  `{ key, correlation }`. Ties go to major, then the lower tonic pitch class. Major tonics are
  named C Db D Eb E F F# G Ab A Bb B, minor tonics C C# D Eb E F F# G G# A Bb B, and `fifths` comes
  from the contract's tables. No notes, or one pitch class only, gives `null`.
- `describe(tune)`: `{ title, key, estimate, range, intervals, density }` from the above.

## Command (`bin/tunekit.js`)

Every subcommand takes `--tune N` to pick the tune with `X:N` (default the first).

- `tunekit tomidi [--format 0|1] [-o OUT] FILE.abc` writes the MIDI file, by default next to the
  input with `.mid`, and prints `wrote OUT (N notes, T ticks)` to stderr.
- `tunekit transpose (--semitones N | --to KEY) [-o OUT] FILE.abc` writes the transposed tune as
  MIDI (default `NAME-KEY.mid`, as `reel-Eb.mid`) and prints `D major -> Eb major` to stdout.
  `--to` takes a key as written in `K:` and moves by the smallest interval, -6 to +5 semitones.
- `tunekit chords FILE.abc` prints one line per bar, `bar<TAB>chord`, naming the pitches of the
  notes starting in the bar, `-` when `nameChord` gives `null`.
- `tunekit analyse [--json] FILE` reads `.abc` or `.mid` by extension and prints `title:`,
  `key:` (written; for MIDI, from the key signature), `estimate:` (key and correlation to two
  decimals), `range:` (as `D4-B5 (21 semitones)`), `intervals:` (as `+2:14 -2:12`) and `density:`
  (the bars' values, space-separated). `--json` prints `describe` as JSON instead.

A `TuneError` prints `FILE:LINE:COL: message` to stderr (`FILE: message` with no position) and
exits 1. A usage error (unknown subcommand or flag, missing file argument) prints a usage line and
exits 2, and so does a file that cannot be read.

## Status

Only the contract exists. Each module gets its own test file in `test/`.
