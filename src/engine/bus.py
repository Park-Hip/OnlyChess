"""The capture event shape Wave 5 listeners will consume."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Capture:
    capturer: object
    captured: object
    displaced: bool


class Bus:
    def __init__(self):
        self._listeners = []

    def listen(self, listener):
        self._listeners.append(listener)

    def emit(self, event):
        actions = []
        for listener in self._listeners:
            result = listener(event)
            if result:
                actions.extend(result)
        return actions
