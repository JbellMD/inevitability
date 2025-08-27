# Memory System Documentation

## Overview

The Memory system in Inevitability provides persistent storage, retrieval, and evaluation of the system's experiences, decisions, and knowledge. It emphasizes remembrance as a key ethical component of AI behavior.

## Components

### Memory Lattice

The Memory Lattice combines vector embeddings and graph-based relationships to create a multi-dimensional memory structure:

- **Vector Storage**: Using Qdrant for semantic similarity searches
- **Hypergraph**: Using SQLite for storing relationship edges
- **Ledger**: Recording events, decisions, and their contexts

### Anamnesis Engine

The Anamnesis Engine (from Greek "ἀνάμνησις" meaning "remembrance") monitors and manages memory retention:

- Computes Remembrance Retention Index (RRI)
- Records and retrieves lessons
- Cites lessons in decisions to improve retention
- Registers decisions with their proofs and assessments

## Integration Points

The Memory system interfaces with:
- Ethics components (recording harm events and externality assessments)
- Proof-Carrying Advice (decisions with verifiable proofs)
- Metrics system (providing RRI for 𝓔/𝒢 calculations)

## Usage

Memory components are used throughout the system to:
- Store and retrieve experiences
- Inform decisions based on past events
- Track ethical indices over time
- Support Remembrance as a key ethical constraint
