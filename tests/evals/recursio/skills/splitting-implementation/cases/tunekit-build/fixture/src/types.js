/**
 * The records the tunekit modules pass to one another.
 * @module
 */

/** Ticks in one quarter note. Divisible by 3 and 16, so triplets and sixteenths are whole ticks. */
export const TICKS_PER_QUARTER = 480;

/** Velocity of a note that carries no accent. */
export const DEFAULT_VELOCITY = 80;

/**
 * The modes a key can be in. "major" is the same scale as "ionian", "minor" as "aeolian".
 * @typedef {"major"|"minor"|"ionian"|"dorian"|"phrygian"|"lydian"|"mixolydian"|"aeolian"|"locrian"} Mode
 */

/** @type {readonly Mode[]} */
export const MODES = Object.freeze([
  "major",
  "minor",
  "ionian",
  "dorian",
  "phrygian",
  "lydian",
  "mixolydian",
  "aeolian",
  "locrian",
]);

/**
 * Sharps (positive) or flats (negative) of each major key, by tonic as written.
 * @type {Readonly<Record<string, number>>}
 */
export const MAJOR_KEY_FIFTHS = Object.freeze({
  Cb: -7,
  Gb: -6,
  Db: -5,
  Ab: -4,
  Eb: -3,
  Bb: -2,
  F: -1,
  C: 0,
  G: 1,
  D: 2,
  A: 3,
  E: 4,
  B: 5,
  "F#": 6,
  "C#": 7,
});

/**
 * How many fifths each mode sits from the major key on the same tonic: A dorian is
 * A major (3) plus dorian (-2), one sharp.
 * @type {Readonly<Record<Mode, number>>}
 */
export const MODE_FIFTHS_OFFSET = Object.freeze({
  major: 0,
  ionian: 0,
  lydian: 1,
  mixolydian: -1,
  dorian: -2,
  minor: -3,
  aeolian: -3,
  phrygian: -4,
  locrian: -5,
});

/** The order sharps are added in; flats are added in the reverse order. */
export const SHARP_ORDER = "FCGDAEB";

/**
 * One sounding note.
 * @typedef {object} Note
 * @property {number} pitch MIDI note number, 0-127; middle C (C4) is 60.
 * @property {number} start Start in ticks from the beginning of the tune.
 * @property {number} duration Length in ticks, at least 1.
 * @property {number} velocity 1-127.
 */

/**
 * A key as written, with its signature worked out.
 * @typedef {object} KeySignature
 * @property {string} tonic A letter with an optional "#" or "b": "C", "F#", "Bb".
 * @property {Mode} mode
 * @property {number} fifths Sharps (positive) or flats (negative) in the signature, -7 to 7.
 */

/**
 * A time signature.
 * @typedef {object} Meter
 * @property {number} beats The numerator: 6 in 6/8.
 * @property {number} unit The denominator, a power of two: 8 in 6/8.
 */

/**
 * One tune.
 * @typedef {object} Tune
 * @property {number} index The tune's reference number (ABC "X:").
 * @property {string} title
 * @property {Meter} meter
 * @property {[number, number]} unitLength The default note length as a fraction: [1, 8].
 * @property {number} tempo Quarter notes per minute.
 * @property {KeySignature} key
 * @property {Note[]} notes Sorted by start, then pitch.
 */

/** A file or value tunekit cannot read. `line` and `column` count from 1 when known. */
export class TuneError extends Error {
  /**
   * @param {string} message
   * @param {number | null} [line]
   * @param {number | null} [column]
   */
  constructor(message, line = null, column = null) {
    super(message);
    this.name = "TuneError";
    this.line = line;
    this.column = column;
  }
}
