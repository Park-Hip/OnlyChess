# Refactor Glossary

| Term | Meaning |
|---|---|
| action | A recorded state change with an inverse. Undo reverses actions, never replays an effect. |
| activation | Selecting linked content as the active game mode after loading succeeds. |
| code mod | A trusted local mod that registers new vocabulary through `ModApi`; it does not directly define privileged content. |
| condition | A pure yes/no predicate over game state. It has no side effects or computation loops. |
| content | Declarative mod data such as a piece, board, status, ability, event, resource, fusion rule, or game mode. |
| data mod | A mod made from declarative content using vocabulary already registered by the engine/code mods. |
| effect | A verb that chooses and emits actions to change game state. |
| engine | The generic core in `src/`: geometry, pipelines, loader, registries, actions, rendering loop, and validation. |
| legacy runtime | The old hardcoded game. It remains available temporarily as an oracle, not as the extension model. |
| link | The loader stage that resolves references between already validated, registered content. |
| mod | A package under `mods/` with a manifest, content files, and optionally trusted code. |
| oracle | The differential tests in `tests/oracle/` that compare the replacement engine against legacy chess behaviour. |
| registry | A runtime-populated, namespaced mapping for content or registered vocabulary. |
| selector | Declarative rule for finding eligible game objects and choosing among them. |
| status | First-class, data-defined state attached to a piece and ticked centrally rather than owned by an event. |
| verb | A reusable engine capability that content can name: move type, effect, condition, or selector. |
