"""HTTP request and response schemas derived from CONTRACT.md v2.1."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ccf_pygame.ccf.drive_chart import DRIVE_CHART
from ccf_pygame.ccf.rules import TABLE_FG

RATING_VALUES = tuple(sorted(int(value) for value in DRIVE_CHART))
KICK_RATING_VALUES = tuple(sorted(TABLE_FG))
MAX_STARTING_CLUTCH = 3
MAX_TEAM_NAME_LENGTH = 40


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class TeamSetup(StrictModel):
    name: str = Field(min_length=1, max_length=MAX_TEAM_NAME_LENGTH)
    rating: int = Field(ge=RATING_VALUES[0], le=RATING_VALUES[-1])
    kick_rating: int = Field(
        ge=KICK_RATING_VALUES[0], le=KICK_RATING_VALUES[-1]
    )
    clutch: int = Field(ge=0, le=MAX_STARTING_CLUTCH)

    @field_validator("name")
    @classmethod
    def name_must_contain_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("name must contain non-whitespace characters")
        return stripped


class HomeSetup(TeamSetup):
    color: Literal["red", "black"]


class AwaySetup(TeamSetup):
    pass


class CreateGameRequest(StrictModel):
    home: HomeSetup
    away: AwaySetup
    difficulty: Literal["easy", "medium", "hard"]
    seed: int | None = None


class PlayCardAction(StrictModel):
    revision: int = Field(ge=0)
    type: Literal["play_card"]
    card_index: int


class PostMoveAction(StrictModel):
    revision: int = Field(ge=0)
    type: Literal["post_move"]
    choice: Literal["P", "F", "C", "S"]


class ExtraPointAction(StrictModel):
    revision: int = Field(ge=0)
    type: Literal["extra_point"]
    choice: Literal["K", "2"]


Action = Annotated[
    PlayCardAction | PostMoveAction | ExtraPointAction,
    Field(discriminator="type"),
]


class GameResponse(BaseModel):
    revision: int
    snapshot: dict[str, Any]
    events: list[dict[str, Any]]


class ReplayResponse(BaseModel):
    seed: int
    events: list[dict[str, Any]]
