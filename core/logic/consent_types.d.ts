// core/logic/consent_types.d.ts
// Consent as *linear capabilities* (single-use or bounded-use), with scope & TTL.
// Any cross-scope escalation without explicit ticket is a type error upstream.

declare namespace Consent {
  // ---------- Scalars ----------
  type ISO8601_Duration = string; // "PT24H", "P7D"
  type EpochSeconds = number;
  type TicketID = string & { readonly brand: unique symbol };

  // ---------- Scopes ----------
  type Scope = "self" | "dyad" | "group" | "org" | "public";
  type ScopeOrder = ReadonlyArray<Scope>; // for lattice comparisons

  interface ScopeLattice {
    readonly order: ScopeOrder; // ["self","dyad","group","org","public"]
    lte(a: Scope, b: Scope): boolean; // whether a ≤ b in lattice
  }

  // ---------- Linear Tickets ----------
  interface Terms {
    readonly purpose: string;            // e.g., "coaching", "deploy", "analysis"
    readonly fields?: ReadonlyArray<string>; // allowed fields/objects by id prefix
    readonly reversible?: boolean;       // required for micro-moves near paradox
    readonly maxInvocations?: number;    // linear usage bound
    readonly nonCoercion?: boolean;      // defaults true; if false -> type error
    readonly confidentiality?: "none" | "private" | "secret";
  }

  interface Ticket {
    readonly id: TicketID;
    readonly holder: string;       // subject granting consent
    readonly scope: Scope;
    readonly issuedAt: EpochSeconds;
    readonly ttl: ISO8601_Duration; // RFC 3339 duration
    readonly terms: Terms;
    readonly signature?: string;   // detached signature (future)
    // Linear state (runtime-kept; not part of signature):
    readonly _uses?: number;       // consumed invocations
  }

  interface Checked<T extends Ticket> {
    readonly ok: true;
    readonly ticket: T;
    readonly remainingInvocations: number;
    readonly expiresAt: EpochSeconds;
  }
  type CheckFail =
    | { ok: false; reason: "expired"; at: EpochSeconds }
    | { ok: false; reason: "no_invocations"; at: EpochSeconds }
    | { ok: false; reason: "scope_violation"; need: Scope; have: Scope }
    | { ok: false; reason: "noncoercion_violation" }
    | { ok: false; reason: "field_violation"; field: string };

  type CheckResult<T extends Ticket> = Checked<T> | CheckFail;

  // ---------- API Surface (to be implemented in TS/Runtime) ----------
  interface API {
    parseTTL(ttl: ISO8601_Duration): number; // seconds
    expiresAt(t: Ticket): EpochSeconds;
    checkScope(lat: ScopeLattice, need: Scope, have: Scope): boolean;
    check(lat: ScopeLattice, t: Ticket, use: { needScope: Scope; field?: string }): CheckResult<Ticket>;
    consume(t: Ticket): Ticket; // increments _uses (immutably)
  }
}

// Augment global to import with `import type { Consent } from "./consent_types";`
export = Consent;
export as namespace Consent;
