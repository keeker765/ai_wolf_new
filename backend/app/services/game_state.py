from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal


class Role(str, Enum):
    WEREWOLF = "W"
    SEER = "S"
    WITCH = "Witch"
    HUNTER = "H"
    VILLAGER = "V"


class Phase(str, Enum):
    INIT = "Init"
    NIGHT = "Night"
    DAY = "Day"
    VOTE = "Vote"
    RESOLVE = "Resolve"
    END = "End"


Role_CONFIGS = {
    6: {"W": 2, "S": 1, "Witch": 1, "H": 0, "V": 2},
    9: {"W": 3, "S": 1, "Witch": 1, "H": 1, "V": 3},
    10: {"W": 3, "S": 1, "Witch": 1, "H": 1, "V": 4},
}


def assign_roles(seats: int) -> dict[int, Role]:
    """Assign roles to seats randomly."""
    config = Role_CONFIGS.get(seats, Role_CONFIGS[9])
    roles = []
    for role_str, count in config.items():
        roles.extend([Role(role_str)] * count)

    random.shuffle(roles)
    return {seat: roles[i] for i, seat in enumerate(range(1, seats + 1))}


@dataclass
class PlayerState:
    seat: int
    user_id: str
    role: Role
    alive: bool = True


@dataclass
class NightState:
    wolf_target: int | None = None
    witch_heal_used: bool = False
    witch_poison_used: bool = False
    witch_heal_target: int | None = None
    witch_poison_target: int | None = None
    seer_check_target: int | None = None
    seer_check_result: bool | None = None


@dataclass
class VoteState:
    ballots: dict[int, int | None] = field(default_factory=dict)  # seat -> target
    revote_count: int = 0


@dataclass
class GameState:
    game_id: str
    room_id: str
    seats: int
    players: dict[int, PlayerState] = field(default_factory=dict)
    phase: Phase = Phase.INIT
    round: int = 0
    night: NightState = field(default_factory=NightState)
    vote: VoteState = field(default_factory=VoteState)
    winner: Literal["villagers", "werewolves", None] = None
    events: list[dict] = field(default_factory=list)

    def add_event(
        self, event_type: str, actor_seat: int | None = None, payload: dict | None = None
    ):
        """Add an event to the game log."""
        event = {
            "seq": len(self.events) + 1,
            "type": event_type,
        }
        if actor_seat is not None:
            event["actor_seat"] = actor_seat
        if payload:
            event["payload"] = payload
        self.events.append(event)

    def alive_players(self) -> list[int]:
        """Get list of alive player seats."""
        return [seat for seat, p in self.players.items() if p.alive]

    def alive_werewolves(self) -> list[int]:
        """Get list of alive werewolf seats."""
        return [seat for seat, p in self.players.items() if p.alive and p.role == Role.WEREWOLF]

    def alive_villagers(self) -> list[int]:
        """Get list of alive non-werewolf seats."""
        return [seat for seat, p in self.players.items() if p.alive and p.role != Role.WEREWOLF]

    def check_victory(self) -> Literal["villagers", "werewolves", None]:
        """Check for victory conditions."""
        wolves = len(self.alive_werewolves())
        villagers = len(self.alive_villagers())

        if wolves == 0:
            return "villagers"
        if wolves >= villagers:
            return "werewolves"
        return None

    def advance_phase(self):
        """Advance to the next phase."""
        if self.phase == Phase.INIT:
            self.phase = Phase.NIGHT
            self.round = 1
        elif self.phase == Phase.NIGHT:
            self.phase = Phase.DAY
        elif self.phase == Phase.DAY:
            self.phase = Phase.VOTE
        elif self.phase == Phase.VOTE:
            self.phase = Phase.RESOLVE
        elif self.phase == Phase.RESOLVE:
            # Check victory
            winner = self.check_victory()
            if winner:
                self.phase = Phase.END
                self.winner = winner
            else:
                self.phase = Phase.NIGHT
                self.round += 1
                # Reset night state
                self.night = NightState()
                self.vote = VoteState()


def create_game(game_id: str, room_id: str, seats: int, members: dict[str, Any]) -> GameState:
    """Create a new game state."""
    role_assignments = assign_roles(seats)

    game = GameState(game_id=game_id, room_id=room_id, seats=seats)

    # Assign players
    for i, (user_id, _member) in enumerate(members.items()):
        seat = i + 1
        role = role_assignments[seat]
        game.players[seat] = PlayerState(seat=seat, user_id=user_id, role=role)
        game.add_event("role_assigned", actor_seat=seat, payload={"role": role.value})

    game.add_event("game_started", payload={"room_id": room_id, "game_id": game_id, "seats": seats})

    return game
