// The records the pkgaudit modules pass to one another.

/** Finding severities, most severe first. */
export const SEVERITIES = ["critical", "high", "moderate", "low", "info"] as const;

export type Severity = (typeof SEVERITIES)[number];

/** One installed package, as a lockfile records it. */
export interface Package {
  name: string;
  version: string;
  /** Where it was fetched from, or null when the lockfile does not say. */
  resolved: string | null;
  /** The Subresource Integrity string, as `sha512-...`, or null. */
  integrity: string | null;
  /** Installed only for development. */
  dev: boolean;
  /** The SPDX license expression as the package declares it, or null when unknown. */
  license: string | null;
  /** Where it sits: `node_modules/a/node_modules/b` for npm, the first specifier for yarn. */
  path: string;
}

/** Something a check found about one package. */
export interface Finding {
  /** The check's id, as `license-denied`. */
  rule: string;
  severity: Severity;
  package: string;
  version: string;
  message: string;
}

/** What a project accepts, read from its policy file. */
export interface Policy {
  /** License ids that pass, as `MIT`; `LicenseRef-*` allows every LicenseRef. */
  allow: string[];
  /** License ids that fail. */
  deny: string[];
  /** A severity per rule id, replacing the rule's default. */
  severity: Partial<Record<string, Severity>>;
  /** Package names, or `name@range`, whose findings are dropped. */
  ignore: string[];
  /** A semver range each named package's installed versions must satisfy. */
  pins: Record<string, string>;
}

/** Input pkgaudit cannot read: a lockfile, range or expression it refuses. */
export class AuditError extends Error {
  /** The file the error is in, when there is one. */
  readonly file: string | null;

  constructor(message: string, file: string | null = null) {
    super(message);
    this.name = "AuditError";
    this.file = file;
  }
}
