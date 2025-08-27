# Metrics System Documentation

## Overview

The Metrics system provides quantitative measures of the system's ethical, aesthetic, and functional performance. These metrics guide decision-making and ensure accountability.

## Core Metrics

### Energy (𝓔)

Energy measures structural integrity and cleanliness:
- **Range**: 0.0 to 1.0 (higher is better)
- **Components**:
  - Consent and apophatic rail adherence
  - Harm penalties
  - Paradox proximity penalties
  - Risk adjustments

### Grace (𝒢)

Grace measures aesthetic coherence and dignity preservation:
- **Range**: 0.0 to 1.0 (higher is better)
- **Components**:
  - Externality coverage
  - Rollback readiness
  - Plan coherence
  - Dignity debt

### Kenosis (K)

Kenosis measures self-emptying readiness and repair follow-through:
- **Range**: 0.0 to 1.0 (higher is better)
- **Components**:
  - Harm repair rate
  - Rollback density
  - De-escalation rate

### Remembrance Retention Index (RRI)

RRI measures the system's ability to retain and apply past lessons:
- **Range**: 0.0 to 1.0 (higher is better)
- Improved by citing lesson atoms in decisions

## Derived Signals

### Stand

Stand recommends whether a decision should be halted:
- Triggered by hard rail failures (consent, apophatic, externalities)
- Triggered by low Energy AND Grace
- Triggered by low RRI

### Throne-Fiber

Throne-Fiber indicates optimal ethical alignment:
- Requires all rails to pass
- Requires Energy, Grace, Kenosis, and RRI all ≥ 0.70

## Integration Points

The Metrics system integrates with:
- Proof-Carrying Advice (for rail validation)
- Ethics components (for harm and externality assessments)
- Memory system (for RRI)
- Dashboard (for visualization)
