"""
Representation of a decision made for an applicant by ubc admissions
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import discord

from Campus import Campus
from Decision import Decision
from UBCProgram import UBCProgram


@dataclass
class ApplicantDecision():
    discord_username: str = None
    discord_id: int = None
    campus: Campus = None
    program: UBCProgram = None
    decision: Decision = None
    decision_date: datetime = None
    international: bool = None
    curriculum: str = None
    average: str = None
    application_date: datetime = None
    comments: Optional[str] = None
    intended_major: Optional[str] = None
    attachment: Optional[discord.Attachment] = None
    msg_id: Optional[int] = None

    @staticmethod
    def from_dict(d: dict):
        a = ApplicantDecision()
        a.discord_username = d["discord_username"]
        a.discord_id = d["discord_id"]
        a.campus = Campus(d["campus"])
        a.program = UBCProgram(d["program"])
        a.decision = Decision(d["decision"])
        a.decision_date = d["decision_date"]
        a.international = d["international"]
        a.curriculum = d["curriculum"]
        a.average = d["average"]
        a.application_date = d["application_date"]
        a.comments = d["comments"]
        a.intended_major = d["intended_major"]
        a.attachment = d["attachment"]
        a.msg_id = d["msg_id"]
        return a

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
            "intended_major": self.intended_major,
            "attachment": self.attachment if self.attachment else None,
            "msg_id": self.msg_id
        }
