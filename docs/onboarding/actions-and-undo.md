# Actions and Undo

This is the central implementation rule:

> Every state change is an action, and every action has an inverse.

An action has `apply(state)` and `undo(state)`. The pipeline applies actions in order, stores the
list in `state.action_log`, and undoes the list in reverse order.

## What belongs in an action

Actions represent concrete consequences, for example:

- `Relocate` — move a piece and restore its previous square/moved flag
- `Remove` — remove a piece and restore it
- `Replace` — transform a piece and restore the old object
- `SetStatus`, `ClearStatus`, `TickStatus`
- `AdjustResource`, `SetSide`, `Swap`
- turn, pool, pending-event, message, and move-history updates

The action records the information needed for its own inverse. Do not ask the effect to explain
itself again during undo.

## Adding a state-changing feature

1. Decide what concrete state changes happen.
2. Add or reuse an action for each change.
3. Make the effect/verb return those actions.
4. Ensure the pipeline includes them in the same record as the triggering operation.
5. Test both the resulting state and the exact restored state after undo.

For random behavior, record the chosen result in the action or resulting action list. Do not rely on
replaying an RNG seed during undo.

## What is forbidden

Do not directly assign board locations, piece sides, statuses, resources, turn ownership, event
queues, or messages from an effect, event, ability, or UI handler. Direct mutation makes complete-turn
undo incomplete and makes unknown mod effects impossible to reverse safely.

`simulate()` is allowed to apply and immediately undo actions for legality checks. It must leave the
state exactly as it found it.

## Testing an action

At minimum, test:

- state before `apply()`;
- expected state after `apply()`;
- state after `undo()` equals the original state;
- repeated apply/undo does not leak objects, statuses, messages, or counters;
- a complete move/ability/event record undoes as one player-visible turn.

Read [the action implementation](../../src/engine/actions.py) and the pipeline before introducing a
new mutation path.
