// core/logic/apophatic_guard.ts
// Apophatic Guard (ApL): prevent positive predication of the Ground.
// Ground cannot be named/owned/measured; only *negative* constraints apply.
// We validate params and context; if an action asserts Ground=X (idolatry), reject.

import type Consent = require("./consent_types");

type KV = Record<string, unknown>;

export interface ApophaticConfig {
  // Keys whose *positive* assertion implies idolatry (forbidden):
  forbiddenPredicates: ReadonlyArray<string>; // e.g., ["ground_is","ultimate_name","claim_of_ownership"]
  // Keys allowed only as *constraints* (negative), not as identities:
  constraintOnly: ReadonlyArray<string>; // e.g., ["no_image","no_totalization"]
  // Allow *witness* style hints (phenomenology) but not objectification:
  phenomenologyKeys: ReadonlyArray<string>; // e.g., ["silence","emptiness","ungraspability"]
}

export interface ApophaticReport {
  apophatic_ok: boolean;
  reasons: string[];
  warnings: string[];
}

const DEFAULTS: ApophaticConfig = {
  forbiddenPredicates: ["ground_is", "ultimate_name", "final_owner", "sovereign_claim"],
  constraintOnly: ["no_image", "no_totalization", "no_equivalence", "no_exchange"],
  phenomenologyKeys: ["silence", "emptiness", "ungraspability", "awe"]
};

// Utility: detect any affirmative predication about Ground/*ultimate*/
function assertiveGroundClaims(obj: KV): string[] {
  const claims: string[] = [];
  const keys = Object.keys(obj || {});
  for (const k of keys) {
    const v = obj[k];
    if (typeof v === "object" && v !== null) {
      claims.push(...assertiveGroundClaims(v as KV));
    }
    const low = k.toLowerCase();
    if (low.includes("ground_is") || low.includes("ultimate_name") || low.includes("final_owner") || low.includes("sovereign_claim")) {
      claims.push(`positive_predication:${k}`);
    }
  }
  return claims;
}

export function admissible(context: KV, params: KV, cfg: Partial<ApophaticConfig> = {}): [boolean, ApophaticReport] {
  const C: ApophaticConfig = { ...DEFAULTS, ...cfg };
  const reasons: string[] = [];
  const warnings: string[] = [];

  // 1) Hard forbiddens
  const hard = assertiveGroundClaims(params);
  for (const f of C.forbiddenPredicates) {
    if (params.hasOwnProperty(f)) hard.push(`explicit_forbidden:${f}`);
  }
  if (hard.length) {
    reasons.push(...hard);
    return [false, { apophatic_ok: false, reasons, warnings }];
  }

  // 2) Constraint-only keys must be boolean/negative, not identities
  for (const ck of C.constraintOnly) {
    if (params.hasOwnProperty(ck)) {
      const v = params[ck];
      const valid = v === true || v === "enforced";
      if (!valid) warnings.push(`constraint_only_violation:${ck}`);
    }
  }

  // 3) Phenomenology is permitted, but cannot be used as object claims
  for (const pk of C.phenomenologyKeys) {
    if (params.hasOwnProperty(pk)) {
      // Soft hint only; fine.
      continue;
    }
  }

  return [true, { apophatic_ok: true, reasons, warnings }];
}

// Example gate (optional): combine with Consent check
export function rails(consent: Consent.CheckResult<Consent.Ticket>, apoph: [boolean, ApophaticReport]) {
  if (!consent || (consent as any).ok !== true) return { ok: false, reason: "consent" };
  if (!apoph[0]) return { ok: false, reason: "apophatic", details: apoph[1] };
  return { ok: true };
}
