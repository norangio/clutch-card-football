from copy import deepcopy

import pytest

from ccf_pygame.ccf.drive_chart import DRIVE_CHART
from ccf_pygame.ccf.rules import TABLE_FG

from web_api.app import create_app
from web_api.store import MemorySessionStore
from web_api.tests.test_api import SETUP, request


def make_app():
    return create_app(
        store=MemorySessionStore(),
        id_factory=lambda: "validation-game",
    )


def setup_with(path, value):
    setup = deepcopy(SETUP)
    target = setup
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    return setup


@pytest.mark.parametrize(
    "path,value",
    [
        (("home", "rating"), min(map(int, DRIVE_CHART))),
        (("home", "rating"), max(map(int, DRIVE_CHART))),
        (("away", "rating"), min(map(int, DRIVE_CHART))),
        (("away", "rating"), max(map(int, DRIVE_CHART))),
        (("home", "kick_rating"), min(TABLE_FG)),
        (("home", "kick_rating"), max(TABLE_FG)),
        (("away", "kick_rating"), min(TABLE_FG)),
        (("away", "kick_rating"), max(TABLE_FG)),
        (("home", "clutch"), 0),
        (("home", "clutch"), 3),
        (("away", "clutch"), 0),
        (("away", "clutch"), 3),
        (("home", "name"), "X" * 40),
        (("difficulty",), "easy"),
        (("difficulty",), "medium"),
        (("difficulty",), "hard"),
        (("home", "color"), "red"),
        (("home", "color"), "black"),
    ],
)
def test_setup_accepts_every_valid_boundary(path, value):
    status, payload = request(
        make_app(), "POST", "/api/games", setup_with(path, value)
    )

    assert status == 200
    assert payload["snapshot"]["game_id"] == "validation-game"


@pytest.mark.parametrize(
    "path,value",
    [
        (("home", "rating"), min(map(int, DRIVE_CHART)) - 1),
        (("home", "rating"), max(map(int, DRIVE_CHART)) + 1),
        (("away", "rating"), 99),
        (("home", "rating"), "6"),
        (("home", "kick_rating"), min(TABLE_FG) - 1),
        (("home", "kick_rating"), max(TABLE_FG) + 1),
        (("away", "kick_rating"), 0),
        (("home", "clutch"), -1),
        (("home", "clutch"), 4),
        (("away", "clutch"), 4),
        (("home", "name"), ""),
        (("home", "name"), "   "),
        (("away", "name"), "X" * 41),
        (("difficulty",), "impossible"),
        (("home", "color"), "orange"),
    ],
)
def test_setup_rejects_invalid_values_as_400_invalid_action(path, value):
    status, payload = request(
        make_app(), "POST", "/api/games", setup_with(path, value)
    )

    assert status == 400
    assert payload["error"]["code"] == "invalid_action"
    assert "seed" not in payload


def test_setup_trims_valid_team_names():
    setup = setup_with(("home", "name"), "  Wolverines  ")

    status, payload = request(make_app(), "POST", "/api/games", setup)

    assert status == 200
    assert payload["snapshot"]["home"]["name"] == "Wolverines"
