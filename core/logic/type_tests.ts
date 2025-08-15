// Minimal smoke tests for rails. Run with ts-node.
import type Consent = require("./consent_types");
import { admissible } from "./apophatic_guard";

const lattice: Consent.ScopeLattice = {
  order: ["self","dyad","group","org","public"],
  lte: (a,b) => (["self","dyad","group","org","public"].indexOf(a) <= ["self","dyad","group","org","public"].indexOf(b))
};

const api: Consent.API = {
  parseTTL: (d) => d === "PT24H" ? 86400 : 604800,
  expiresAt: (t) => t.issuedAt + api.parseTTL(t.ttl),
  checkScope: (lat, need, have) => lat.lte(have, need),
  check: (lat, t, use) => {
    if (Date.now()/1000 > api.expiresAt(t)) return { ok:false, reason:"expired", at: Date.now()/1000 };
    if (!api.checkScope(lat, use.needScope, t.scope)) return { ok:false, reason:"scope_violation", need: use.needScope, have: t.scope };
    if (t.terms.nonCoercion === false) return { ok:false, reason:"noncoercion_violation" };
    const uses = (t as any)._uses || 0;
    const max = t.terms.maxInvocations ?? 1;
    if (uses >= max) return { ok:false, reason:"no_invocations", at: Date.now()/1000 };
    return { ok:true, ticket: t, remainingInvocations: max-uses, expiresAt: api.expiresAt(t) };
  },
  consume: (t) => Object.freeze({ ...t, _uses: ((t as any)._uses || 0) + 1 })
};

const ticket: Consent.Ticket = Object.freeze({
  id: "t1" as Consent.TicketID,
  holder: "user",
  scope: "dyad",
  issuedAt: Math.floor(Date.now()/1000),
  ttl: "PT24H",
  terms: { purpose: "advice", nonCoercion: true, maxInvocations: 2 }
});

const ok = api.check(lattice, ticket, { needScope: "dyad" });
console.log("consent check:", ok);

const [ap_ok, report] = admissible({}, { no_image: true, silence: "felt" });
console.log("apophatic:", ap_ok, report);
