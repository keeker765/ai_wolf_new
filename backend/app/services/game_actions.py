from __future__ import annotations

from app.core.errors import DomainError
from app.services.game_state import GameState, Phase, Role
from app.services.vote import leaders_of, tally


def handle_wolf_kill(game: GameState, actor_seat: int, target_seat: int):
    """Handle werewolf kill action."""
    if game.phase != Phase.NIGHT:
        raise DomainError(code="GAME_PHASE_ERROR", http_status=409, message="not night phase")

    player = game.players.get(actor_seat)
    if not player or not player.alive:
        raise DomainError(code="GAME_INVALID_ACTION", http_status=400, message="player not alive")

    if player.role != Role.WEREWOLF:
        raise DomainError(code="GAME_INVALID_ACTION", http_status=403, message="not a werewolf")

    target = game.players.get(target_seat)
    if not target or not target.alive:
        raise DomainError(code="GAME_INVALID_ACTION", http_status=400, message="invalid target")

    game.night.wolf_target = target_seat
    game.add_event("wolf_kill_chosen", actor_seat=actor_seat, payload={"target": target_seat})


def handle_witch_heal(game: GameState, actor_seat: int, target_seat: int):
    """Handle witch heal action."""
    if game.phase != Phase.NIGHT:
        raise DomainError(code="GAME_PHASE_ERROR", http_status=409, message="not night phase")

    player = game.players.get(actor_seat)
    if not player or not player.alive:
        raise DomainError(code="GAME_INVALID_ACTION", http_status=400, message="player not alive")

    if player.role != Role.WITCH:
        raise DomainError(code="GAME_INVALID_ACTION", http_status=403, message="not a witch")

    if game.night.witch_heal_used:
        raise DomainError(code="GAME_INVALID_ACTION", http_status=400, message="heal already used")

    game.night.witch_heal_used = True
    game.night.witch_heal_target = target_seat
    self_heal = target_seat == actor_seat
    game.add_event(
        "witch_heal_used",
        actor_seat=actor_seat,
        payload={"target": target_seat, "self_heal": self_heal},
    )


def handle_witch_poison(game: GameState, actor_seat: int, target_seat: int):
    """Handle witch poison action."""
    if game.phase != Phase.NIGHT:
        raise DomainError(code="GAME_PHASE_ERROR", http_status=409, message="not night phase")

    player = game.players.get(actor_seat)
    if not player or not player.alive:
        raise DomainError(code="GAME_INVALID_ACTION", http_status=400, message="player not alive")

    if player.role != Role.WITCH:
        raise DomainError(code="GAME_INVALID_ACTION", http_status=403, message="not a witch")

    if game.night.witch_poison_used:
        raise DomainError(
            code="GAME_INVALID_ACTION", http_status=400, message="poison already used"
        )

    target = game.players.get(target_seat)
    if not target or not target.alive:
        raise DomainError(code="GAME_INVALID_ACTION", http_status=400, message="invalid target")

    game.night.witch_poison_used = True
    game.night.witch_poison_target = target_seat
    game.add_event("witch_poison_used", actor_seat=actor_seat, payload={"target": target_seat})


def handle_seer_check(game: GameState, actor_seat: int, target_seat: int):
    """Handle seer check action."""
    if game.phase != Phase.NIGHT:
        raise DomainError(code="GAME_PHASE_ERROR", http_status=409, message="not night phase")

    player = game.players.get(actor_seat)
    if not player or not player.alive:
        raise DomainError(code="GAME_INVALID_ACTION", http_status=400, message="player not alive")

    if player.role != Role.SEER:
        raise DomainError(code="GAME_INVALID_ACTION", http_status=403, message="not a seer")

    target = game.players.get(target_seat)
    if not target or not target.alive:
        raise DomainError(code="GAME_INVALID_ACTION", http_status=400, message="invalid target")

    is_wolf = target.role == Role.WEREWOLF
    game.night.seer_check_target = target_seat
    game.night.seer_check_result = is_wolf
    game.add_event(
        "seer_checked", actor_seat=actor_seat, payload={"target": target_seat, "is_wolf": is_wolf}
    )


def handle_vote(game: GameState, actor_seat: int, target_seat: int | None):
    """Handle vote action."""
    if game.phase != Phase.VOTE:
        raise DomainError(code="GAME_PHASE_ERROR", http_status=409, message="not vote phase")

    player = game.players.get(actor_seat)
    if not player or not player.alive:
        raise DomainError(code="GAME_INVALID_ACTION", http_status=400, message="player not alive")

    if target_seat is not None:
        target = game.players.get(target_seat)
        if not target or not target.alive:
            raise DomainError(code="GAME_INVALID_ACTION", http_status=400, message="invalid target")

    game.vote.ballots[actor_seat] = target_seat
    game.add_event("vote_cast", actor_seat=actor_seat, payload={"target": target_seat})


def resolve_night(game: GameState):
    """Resolve night actions and determine deaths."""
    deaths = set()

    # Wolf kill
    if game.night.wolf_target:
        # Check if healed
        if game.night.witch_heal_target != game.night.wolf_target:
            deaths.add(game.night.wolf_target)

    # Witch poison
    if game.night.witch_poison_target:
        deaths.add(game.night.witch_poison_target)

    # Apply deaths
    for seat in deaths:
        game.players[seat].alive = False

        # Hunter can shoot if killed at night (configurable, default=true)
        if game.players[seat].role == Role.HUNTER:
            # TODO: Implement hunter shot logic
            pass

    return list(deaths)


def resolve_vote(game: GameState) -> dict:
    """Resolve vote and determine if someone is lynched."""
    counts = tally(game.vote.ballots)
    leaders, top_count = leaders_of(counts)

    # Check for tie
    if len(leaders) > 1:
        if game.vote.revote_count == 0:
            # First tie, trigger revote
            game.add_event(
                "lynch_result", payload={"top": leaders, "tie": True, "action": "revote"}
            )
            game.vote.revote_count = 1
            game.vote.ballots = {}  # Clear ballots for revote
            return {"action": "revote", "leaders": leaders}
        else:
            # Second tie, no lynch (default policy)
            game.add_event(
                "lynch_result", payload={"top": leaders, "tie": True, "action": "no_lynch"}
            )
            return {"action": "no_lynch", "leaders": leaders}

    # Single leader, execute
    executed = leaders[0] if leaders else None
    if executed:
        game.players[executed].alive = False
        game.add_event("lynch_result", payload={"executed": executed})

        # Hunter can shoot if lynched
        if game.players[executed].role == Role.HUNTER:
            # TODO: Implement hunter shot logic
            pass

    return {"action": "lynch", "executed": executed}
