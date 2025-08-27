# Inevitability AI Framework

## Overview

Inevitability is a multi-agent AI system designed for ethical, accountable AI behavior through a modular architecture of services. The framework emphasizes ethical rails, consent mechanisms, memory retention, and transparent decision-making processes.

## Architecture

The system consists of several interconnected modules:

- **Core Services**
  - **Interactant**: Primary user-facing agent
  - **Counsel**: Reflective advisory module
  - **Contemplator**: Higher-order reasoning with Shadow Twin adversarial checks
  - **Memory Lattice**: Hypergraph-based memory system with anamnesis (remembrance)

- **Supporting Services**
  - **Ethics/Economics**: Harms Ledger and Externality Pricer
  - **Proofs**: Proof-Carrying Advice for verifiable ethics
  - **Metrics**: 𝓔 (Energy), 𝒢 (Grace), Kenosis, and RRI tracking
  - **Dashboard**: Real-time metrics visualization

## Key Components

### Ethics System
- **Harms Ledger**: Tracks potential and actual harms with severity and malice vectors
- **Externality Pricer**: Quantifies positive and negative externalities of actions

### Memory System
- **Memory Lattice**: Integrates vector embeddings (Qdrant) and graph relationships (SQLite)
- **Anamnesis Engine**: Maintains Remembrance Retention Index (RRI)

### Decision System
- **Proof-Carrying Advice**: Ensures decisions carry verifiable ethics proofs
- **Shadow Twin**: Adversarial testing through will-axis inversion
- **Decision Core**: Lexicographic decision-making using 𝓔 and 𝒢 metrics

### Metrics
- **Energy (𝓔)**: Measures structural integrity and consent adherence
- **Grace (𝒢)**: Measures aesthetic coherence and dignity preservation
- **Kenosis**: Measures self-emptying readiness and repair follow-through
- **Trackers**: Computes Stand/Throne-Fiber signals

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Available ports for services (6333, 6334, 8501)

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/JbellMD/inevitability.git
   cd inevitability
   ```

2. Launch the services:
   ```
   cd deploy
   docker-compose up -d
   ```

3. Access the dashboard:
   - Direct: http://localhost:8501
   - With Caddy (optional): https://inevitability.local

## Development

The project uses a monorepo structure with Python, TypeScript, and YAML configurations. All core logic is implemented in modular services that can be independently tested and deployed.

## License

[License details to be added]
