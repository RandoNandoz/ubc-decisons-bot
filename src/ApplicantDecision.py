"""
Representation of a decision made for an applicant by ubc admissions
"""

import Decision
import Campus
import UBCProgram
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class ApplicantDecision:
    discord_username: str
    discord_id: int
    campus: Campus
    program: UBCProgram
    decision: Decision
    decision_date: datetime
    international: bool
    curriculum: str
    average: str
    application_date: datetime
    comments: Optional[str]
    intended_major: Optional[str]

    def __dict__(self):
        return {
            "discord_username": self.discord_username,
            "discord_id": self.discord_id,
            "campus": self.campus.value,
            "program": self.program.value,
            "decision": self.decision.value,
            "decision_date": self.decision_date,
            "international": self.international,
            "curriculum": self.curriculum,
            "average": self.average,
            "application_date": self.application_date,
            "comments": self.comments,
            "intended_major": self.intended_major
        }

