---
description: Enforces deterministic Multi-Agent Orchestration (Architect, Parallel Workers, and Adversarial QA Critic) for all multi-file tasks.
trigger: always_on
---

# Antigravity Workspace Orchestration Rules

1. **No Code Before Blueprint**: For any task touching 2+ files or introducing a new feature, the primary agent (`Master Orchestrator`) MUST first generate or update `plans/architecture-spec.md` via the **Technical Architect** role before writing implementation code.
2. **Strict Role Separation**:
   - **Architect Role**: Owns file structure, routing patterns, data contracts, and API schemas.
   - **Ingestion / Backend Worker**: Owns data fetching, XML/JSON parsing, file system operations, and external API integrations.
   - **UI / Theme Worker**: Owns HTML templates, CSS/Tailwind styling, responsive layout, and interactive client-side state.
   - **SEO & DevOps Worker**: Owns `robots.txt`, `sitemap.xml`, JSON-LD structured data, OpenGraph tags, and GitHub REST/Git Data API deployment.
   - **QA Critic Role**: Must run automated verification scripts and audit every requirement before the Orchestrator finishes the turn.
3. **Zero Placeholder Policy**: Subagents are strictly forbidden from outputting `TODO`, `FIXME`, `pass`, `// ...`, or mock stubs where functional logic is requested.
4. **Shared Transcript & Handoff Hygiene**: Every subagent must read `plans/architecture-spec.md` on startup and append a concise completion log (`File Path`, `Key Exports`, `Verification Status`) to `plans/master-task-board.md`.
