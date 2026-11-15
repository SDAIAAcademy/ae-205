"""The request and response contract of /v1/triage and /v1/similar (see CONTRACT.md)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Line = Literal["motor", "health", "property"]
Region = Literal["riyadh", "makkah", "eastern", "madinah", "qassim", "asir"]
Channel = Literal["app", "branch", "broker"]
Label = Literal["fast_track", "standard", "investigate"]


class Member(BaseModel):
    """Personal data: accepted, never logged, never sent to the model."""
    model_config = ConfigDict(extra="forbid")
    name: str = Field(max_length=120)
    national_id: str = Field(pattern=r"^[12]\d{9}$")
    mobile: str = Field(pattern=r"^05\d{8}$")


class Claim(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claim_id: str = Field(pattern=r"^CLM-\d{6}$")
    line: Line
    region: Region
    channel: Channel
    amount_sar: float = Field(gt=0, le=5_000_000)
    policy_tenure_months: int = Field(ge=0, le=600)
    prior_claims_12m: int = Field(ge=0, le=50)
    days_to_report: int = Field(ge=0, le=365)
    vehicle_age_years: int | None = Field(default=None, ge=0, le=60)
    police_report: bool | None = None
    in_network: bool | None = None
    description: str = Field(default="", max_length=2000)
    member: Member | None = None

    @model_validator(mode="after")
    def by_line(self) -> "Claim":
        if self.line == "motor" and (self.vehicle_age_years is None or self.police_report is None):
            raise ValueError("a motor claim needs vehicle_age_years and police_report")
        if self.line == "health" and self.in_network is None:
            raise ValueError("a health claim needs in_network")
        return self

    def model_view(self) -> dict:
        """What the model may see: the claim without its personal fields and free text."""
        return self.model_dump(exclude={"member", "description"})


class ModelInfo(BaseModel):
    name: str
    version: str


class Triage(BaseModel):
    claim_id: str
    label: Label
    probabilities: dict[Label, float]
    model: ModelInfo


class SimilarQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: str = Field(min_length=3, max_length=2000)
    line: Line | None = None
    k: int = Field(default=5, ge=1, le=20)


class Neighbour(BaseModel):
    claim_id: str
    line: Line
    incident: str
    score: float


class Similar(BaseModel):
    results: list[Neighbour]
    model: ModelInfo
