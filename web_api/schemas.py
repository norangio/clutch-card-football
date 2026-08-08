"""HTTP request and response schemas derived from CONTRACT.md v2.1."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HomeSetup(StrictModel):
    name: str = Field(min_length=1)
    rating: int
    kick_rating: int
    color: Literal["red", "black"]
    clutch: int


class AwaySetup(StrictModel):
    name: str = Field(min_length=1)
    rating: int
    kick_rating: int
    clutch: int


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
