// The records the subtool modules pass to one another.

/** The subtitle formats subtool reads and writes. */
export const FORMATS = ["srt", "vtt", "ass"] as const;

export type Format = (typeof FORMATS)[number];

/** Horizontal alignment of a cue, as WebVTT names it. */
export const ALIGNMENTS = ["start", "center", "end", "left", "right"] as const;

export type Align = (typeof ALIGNMENTS)[number];

/** Where a cue sits on screen. `line`, `position` and `size` keep WebVTT's text, as `"10%"`. */
export interface Position {
  align: Align;
  line: string | null;
  position: string | null;
  size: string | null;
  region: string | null;
}

/**
 * One subtitle. Times are whole milliseconds from the start of the video. `lines` hold the text,
 * one entry per screen line, with only `<i>`, `<b>` and `<u>` (and their closing tags) as markup.
 */
export interface Cue {
  start: number;
  end: number;
  lines: string[];
  /** The cue's identifier: an SRT index or a WebVTT cue id. */
  id?: string;
  /** The name of an ASS style in the track's `styles`. */
  style?: string;
  position?: Position;
}

/** An ASS style, the fields subtool keeps. Colors are `#RRGGBB`; alpha 0 is opaque. */
export interface Style {
  name: string;
  fontName: string;
  fontSize: number;
  color: string;
  alpha: number;
  bold: boolean;
  italic: boolean;
  underline: boolean;
  /** Numpad alignment, 1-9: 2 is bottom center. */
  alignment: number;
  marginL: number;
  marginR: number;
  marginV: number;
}

/** A WebVTT region: its id and its settings as written, as `{ width: "40%" }`. */
export interface Region {
  id: string;
  settings: Record<string, string>;
}

/** A whole subtitle file in subtool's common form. */
export interface Track {
  cues: Cue[];
  styles: Style[];
  /** WebVTT STYLE blocks, the CSS text of each. */
  css: string[];
  regions: Region[];
  /** Header fields: WebVTT header lines, ASS Script Info. */
  metadata: Record<string, string>;
}

/** A line a reader could not use; `line` counts from 1. */
export interface ParseError {
  line: number;
  message: string;
}

/** What every reader returns: what it could read, and what it skipped. */
export interface ParseResult {
  track: Track;
  errors: ParseError[];
}

/** Readability limits, the defaults every check and the layout use. */
export const DEFAULT_LIMITS = Object.freeze({
  maxLineLength: 42,
  maxLines: 2,
  minDurationMs: 833,
  minGapMs: 83,
  maxCps: 17,
});

export type Limits = typeof DEFAULT_LIMITS;
