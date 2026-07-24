# ADR-001: Selection of LangGraph for Agent Pipeline Orchestration

- **Status**: Accepted
- **Date**: 2026-07-23
- **Deciders**: Architecture Team

---

# Context

CivicConnect relies on multi-step AI reasoning to process citizen reports (forensics, classification, geolocation validation, moderation, enhancement, routing, notification, audit). We needed an agent framework that supports stateful, multi-agent coordination with cyclic state graphs, fallback logic, parallel execution, and strict auditability.

# Considered Options

1. **Custom Python Async State Machine**: Low overhead, but requires building complex graph orchestration, memory management, and DAG visualization from scratch.
2. **AutoGPT / CrewAI**: High abstraction, but lacks fine-grained deterministic execution controls and state isolation necessary for civic government governance.
3. **LangGraph**: Stateful, multi-agent orchestration framework built on top of LangChain, supporting explicit supervisor graphs, parallel node execution, and native LangSmith tracing.

# Decision

We selected **LangGraph** for building the AI agent pipeline.

# Rationale

- **Supervisor Pattern**: Allows a dedicated Supervisor agent node to strictly control execution flow without agents invoking each other directly.
- **Parallel Node Support**: Forensics, Classification, Geo Validation, and Moderation can execute concurrently, minimizing report validation latency.
- **Explicit Shared State**: Pydantic/TypedDict state enforces boundaries where agents can only write to designated state keys.
- **Observability**: Seamless integration with LangSmith for agent trace monitoring and accuracy auditing.

# Consequences

- **Positive**: Strict execution contracts, parallelization, clear audit trail per agent node.
- **Negative**: Adds LangGraph framework dependency; requires careful state key immutability management.
