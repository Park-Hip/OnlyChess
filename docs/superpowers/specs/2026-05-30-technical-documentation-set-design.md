# Chess Fusion Technical Documentation Set Design

## Goal

Define a small, presentation-ready technical documentation set for the Chess Fusion project that helps the team:

- understand how the current system works
- explain the architecture clearly
- highlight the project's OOP design decisions
- navigate the codebase quickly during development and presentation preparation

This spec is for documentation structure and content only. It does not change gameplay behavior or code architecture.

## Audience

Primary audience:

- project team members

Secondary use:

- presentation support for explaining the system to others

Because the main audience is the team, the docs should optimize for technical clarity first. Because the team also needs to present the project, the docs must make OOP decisions easy to explain with examples from the actual codebase.

## Context

The repository already contains:

- a top-level `README.md`
- a high-level architecture note in `docs/architecture-current-baseline.md`
- many implementation planning documents under `docs/*/plans/` and `docs/superpowers/plans/`

What is missing is a focused technical documentation set that explains the current implemented system as a working architecture, not just as a sequence of refactor or feature plans.

## Problem Statement

The current docs are useful for tracking project phases, but they do not yet form a clean technical knowledge base for teammates. Important understanding is still spread across:

- source files
- test files
- planning documents
- implicit knowledge from recent implementation work

This makes it harder to:

- onboard teammates into the current codebase
- present the architecture confidently
- explain how the OOP design supports extension
- quickly find the right files when modifying a subsystem

## Documentation Design Principles

The documentation set should follow these principles:

1. Keep the structure small and readable.
2. Explain the real implemented system, not hypothetical future systems.
3. Highlight OOP decisions explicitly rather than assuming readers will infer them.
4. Show boundaries and interactions between subsystems.
5. Map concepts to actual files and classes in the repository.
6. Prefer practical diagrams, flows, and file references over abstract theory.
7. Avoid overexplaining standard Python syntax or generic OOP textbook material.

## Recommended Documentation Set

The documentation set should contain the following files:

1. `docs/system-overview.md`
2. `docs/oop-design.md`
3. `docs/file-map.md`
4. `docs/game-domain.md`
5. `docs/events-system.md`
6. `docs/fusion-system.md`
7. `docs/abilities-system.md`
8. `docs/ui-and-input.md`
9. `docs/presentation-summary.md`

These files should work together as a layered set:

- one entry point
- one OOP-focused explanation
- one file navigation guide
- one document per major subsystem
- one presentation-oriented summary

## Proposed Information Architecture

### 1. `docs/system-overview.md`

Purpose:

- act as the main entry point for the whole documentation set

This document should include:

- short project description
- gameplay systems currently implemented
- high-level package structure
- runtime flow from game startup to move resolution
- subsystem interaction summary
- quick links to all deeper technical docs

This document should answer:

- what exists in the current system?
- what are the major parts?
- where should a reader go next?

### 2. `docs/oop-design.md`

Purpose:

- explicitly explain the OOP design choices in the project

This document should include:

- core classes and their responsibilities
- where inheritance is used
- where composition is used
- where registries are used
- how responsibilities are separated
- examples of encapsulation, single responsibility, and extension points
- explanation of how the project avoids a God Object

This document should answer:

- how is OOP applied in this project?
- why was this structure chosen?
- how does the code stay understandable and extensible?

This is one of the highest-priority docs for the team presentation.

### 3. `docs/file-map.md`

Purpose:

- give teammates a practical guide to the codebase layout

This document should include:

- folder-by-folder breakdown of `src/`
- important files in each package
- what each file owns
- what each file interacts with
- where to start when changing a feature

This document should answer:

- where is the logic for X?
- which file should I read first?
- which files are safe to change for a given subsystem?

### 4. `docs/game-domain.md`

Purpose:

- explain the core engine and chess-domain logic

This document should include:

- role of `GameState`
- role of `Board`
- role of `Move`
- legal move generation flow
- simulation and rollback
- castling, en passant, promotion, scoring, capture tracking
- boundaries between domain logic and non-domain systems

This document should answer:

- how does the main chess engine work?
- what does `GameState` coordinate versus own directly?
- how does the engine remain side-effect safe during move validation?

### 5. `docs/events-system.md`

Purpose:

- explain the event subsystem as a full technical feature

This document should include:

- purpose of the event system
- `ChessEvent` contract
- registry-based event creation
- `EventManager` lifecycle and timing
- warning phase, execution phase, timed events, cleanup
- interaction with board state and UI overlays
- list of implemented events
- how to add a new event safely

This document should answer:

- how are events scheduled?
- how does a concrete event work?
- which files are involved when building or debugging an event?

### 6. `docs/fusion-system.md`

Purpose:

- explain capture-triggered fusion and fused pieces

This document should include:

- fusion rule concept
- when fusion can happen
- role of `FusionManager`
- mapping of valid fusion pairs
- fused pieces and their movement behavior
- Tempo Burst interaction
- boundaries with capture tracking, events, and abilities

This document should answer:

- when does fusion trigger?
- how are fused pieces represented?
- what files must be updated to add or change fusion rules?

### 7. `docs/abilities-system.md`

Purpose:

- explain the active ability and Action Point architecture

This document should include:

- Action Point purpose and lifecycle
- ability base class
- ability registry
- current abilities and their responsibilities
- how an ability consumes AP and ends or affects a turn
- interactions with move flow and capture summaries

This document should answer:

- how do abilities fit into the turn system?
- where is AP tracked?
- how do new abilities plug into the current design?

### 8. `docs/ui-and-input.md`

Purpose:

- explain the boundary between UI and gameplay logic

This document should include:

- UI package responsibilities
- rendering helpers
- input handling flow
- promotion and ability menu behavior
- what the UI is allowed to do
- what the UI must delegate to domain logic

This document should answer:

- how does user input become game actions?
- where is rendering separated from rules?
- how does this design support maintainability?

### 9. `docs/presentation-summary.md`

Purpose:

- provide a presentation-ready summary that the team can quickly turn into slides or speaking points

This document should include:

- short project summary
- architecture summary
- OOP highlights
- subsystem highlights
- extension and maintainability points
- suggested slide structure

This document should answer:

- what should we say in the presentation?
- what design points are worth emphasizing?
- how do we explain the project clearly in limited time?

## Required Cross-Cutting Sections

Each subsystem document should use a consistent internal structure where possible. The recommended section pattern is:

1. Purpose
2. Responsibility
3. Main classes and files
4. Runtime flow
5. Interactions with other subsystems
6. OOP design notes
7. Extension points
8. Risks, limitations, or cautions

This consistency will make the documentation easier to scan and easier to present as a coherent design.

## OOP Points That Must Be Explicitly Highlighted

The documentation set must clearly highlight these design themes:

### Separation of responsibilities

Examples that should be documented:

- `GameState` coordinates systems but does not contain every subsystem's internal logic
- pieces own movement behavior
- events own event-specific behavior
- managers own orchestration
- UI helpers handle rendering and input state, not rule enforcement

### Basic extensibility

Examples that should be documented:

- adding a new event through a new event class plus registry wiring
- adding a new ability through a new ability class plus registry wiring
- adding new fused pieces through fusion rules and piece classes

### Avoiding overengineering

Examples that should be documented:

- simple inheritance instead of overly deep hierarchies
- direct registries instead of complex factories
- focused helpers instead of a giant all-knowing game class

### Encapsulation and boundaries

Examples that should be documented:

- board access flowing through board helper methods
- UI code using public game state rather than embedding rule logic
- domain systems interacting through controlled methods rather than random global mutation

### Testability

Examples that should be documented:

- registry tests
- event manager flow tests
- subsystem-focused tests for events, pieces, fusion, abilities, and UI helpers

## File Coverage Expectations

The docs should map concepts to the real source tree, especially:

- `src/game/`
- `src/pieces/`
- `src/events/`
- `src/fusion/`
- `src/abilities/`
- `src/ui/`
- `src/main.py`
- `src/constants.py`

The docs do not need to document every private helper equally, but they should mention the most important files and class-level responsibilities inside each subsystem.

## Relationship to Existing Docs

The new documentation set should:

- reuse the current architecture note where helpful
- avoid duplicating old phase-plan detail
- treat planning docs as historical implementation references, not as the main technical explanation

`README.md` should remain a short entry document. The deeper technical explanation should live in the new docs.

## Out of Scope

This documentation set should not try to include:

- a full rewrite of all older planning documents
- detailed code comments copied into documentation
- tutorial-style beginner Python lessons
- speculative future features that are not implemented
- heavy UML for every class in the project

## Deliverables

The final documentation work based on this spec should produce:

- one documentation entry point
- one OOP-focused design explanation
- one file navigation guide
- five subsystem-focused technical documents
- one presentation support document

## Success Criteria

This documentation set is successful if:

1. A teammate can identify where a subsystem lives without reading the whole codebase.
2. A teammate can explain the responsibilities of the main packages and classes.
3. The team can use the docs to prepare architecture and OOP presentation slides.
4. The docs clearly show how the design supports adding new features.
5. The docs make system boundaries explicit, especially between game logic and UI.
6. The documentation remains grounded in the actual implemented code.

## Recommended Writing Order

To produce the docs efficiently, the recommended order is:

1. `docs/system-overview.md`
2. `docs/oop-design.md`
3. `docs/file-map.md`
4. `docs/game-domain.md`
5. `docs/events-system.md`
6. `docs/fusion-system.md`
7. `docs/abilities-system.md`
8. `docs/ui-and-input.md`
9. `docs/presentation-summary.md`

This order builds the shared mental model first, then adds subsystem detail, then finishes with presentation support.

## Recommended Next Step

After this spec is approved, the next step should be to create an implementation plan for writing the documentation set file by file, starting with the overview, OOP design, and file map documents.
