"""Simple registry helpers for concrete event classes."""

import random


_EVENT_REGISTRY = {}


def register_event(event_class):
    """Register a concrete event class by its stable event key."""
    _EVENT_REGISTRY[event_class.event_key] = event_class
    return event_class


def get_event_class(event_key):
    """Return the registered event class for a given key."""
    return _EVENT_REGISTRY[event_key]


def create_event(event_key, game_state):
    """Instantiate an event from its registered key."""
    return get_event_class(event_key)(game_state)


def get_registered_event_keys():
    """Return the currently registered event keys."""
    return list(_EVENT_REGISTRY.keys())


def choose_random_event_key(event_keys):
    """Pick one event key from the available event pool."""
    return random.choice(event_keys)
