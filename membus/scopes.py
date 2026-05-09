from enum import Enum


class Scope(str, Enum):
    """
    The four memory scopes supported by MemBus.

    - USER    : persists across all sessions for a given user
    - SESSION : lives for the duration of one conversation
    - AGENT   : memories tied to an agent's identity or role
    - ORG     : shared across all users in a team or organisation
    """
    USER = "user"
    SESSION = "session"
    AGENT = "agent"
    ORG = "org"
