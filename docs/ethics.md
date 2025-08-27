# Ethics Subsystem Documentation

## Overview

The Inevitability Ethics subsystem provides frameworks for tracking potential harms, calculating externalities, and ensuring ethical decision-making. It consists of several interconnected components that work together to implement ethical rails for the system.

## Components

### Harms Ledger

The Harms Ledger tracks incidents where the system may cause or has caused harm. Each harm event includes:

- Severity: Impact magnitude
- Malice: Intentionality factor
- Resolution status
- Mitigation steps
- Notes and attribution

It computes harm indices (H) that inform Energy (𝓔) and Grace (𝒢) metrics.

### Externality Pricer

The Externality Pricer quantifies the side effects of actions that may impact parties other than the primary agents. It considers:

- Positive and negative externalities
- Magnitude of impact
- Beneficiary and harmed party counts
- Coverage metrics for decision-making
- Rollback readiness assessments

## Integration Points

The Ethics subsystem interfaces with:
- Proof-Carrying Advice system (for verifiable ethics proofs)
- Memory Lattice (for recording ethical events)
- Metrics system (providing penalties that affect 𝓔 and 𝒢)

## Usage

Ethics components are instantiated and used throughout the decision-making pipeline to ensure actions adhere to ethical constraints, maintain high Energy and Grace scores, and support the Stand/Throne-Fiber heuristic signals.
