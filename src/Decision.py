"""
Enum for a university decision
"""

from enum import Enum


class Decision(Enum):
    ACCEPTED = "Accepted"
    WAITLISTED = "Waitlisted"
    REJECTED = "Rejected"
