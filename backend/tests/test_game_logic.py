from app.services.game_state import (
    GameState,
    Phase,
    PlayerState,
    Role,
    assign_roles,
    create_game,
)
from app.services.vote import leaders_of, tally


def test_assign_roles_6():
    roles = assign_roles(6)
    assert len(roles) == 6
    role_counts = {}
    for role in roles.values():
        role_counts[role] = role_counts.get(role, 0) + 1
    assert role_counts[Role.WEREWOLF] == 2
    assert role_counts[Role.SEER] == 1
    assert role_counts[Role.WITCH] == 1
    assert role_counts[Role.VILLAGER] == 2


def test_assign_roles_9():
    roles = assign_roles(9)
    assert len(roles) == 9
    role_counts = {}
    for role in roles.values():
        role_counts[role] = role_counts.get(role, 0) + 1
    assert role_counts[Role.WEREWOLF] == 3
    assert role_counts[Role.SEER] == 1
    assert role_counts[Role.WITCH] == 1
    assert role_counts[Role.HUNTER] == 1
    assert role_counts[Role.VILLAGER] == 3


def test_create_game():
    members = {"user1": None, "user2": None, "user3": None}
    game = create_game("g1", "r1", 6, members)
    assert game.game_id == "g1"
    assert game.room_id == "r1"
    assert game.seats == 6
    assert len(game.players) == 3  # Only 3 members provided
    assert game.phase == Phase.INIT
    assert game.round == 0


def test_game_advance_phase():
    game = GameState(game_id="g1", room_id="r1", seats=6)
    game.players[1] = PlayerState(seat=1, user_id="u1", role=Role.WEREWOLF)
    game.players[2] = PlayerState(seat=2, user_id="u2", role=Role.VILLAGER)
    game.players[3] = PlayerState(seat=3, user_id="u3", role=Role.VILLAGER)

    assert game.phase == Phase.INIT
    game.advance_phase()
    assert game.phase == Phase.NIGHT
    assert game.round == 1

    game.advance_phase()
    assert game.phase == Phase.DAY

    game.advance_phase()
    assert game.phase == Phase.VOTE

    game.advance_phase()
    assert game.phase == Phase.RESOLVE

    game.advance_phase()
    # Should go back to night (game ongoing: 1 wolf, 2 villagers)
    assert game.phase == Phase.NIGHT
    assert game.round == 2


def test_game_check_victory_wolves_win():
    game = GameState(game_id="g1", room_id="r1", seats=6)
    game.players[1] = PlayerState(seat=1, user_id="u1", role=Role.WEREWOLF, alive=True)
    game.players[2] = PlayerState(seat=2, user_id="u2", role=Role.VILLAGER, alive=True)

    # Wolves >= villagers
    winner = game.check_victory()
    assert winner == "werewolves"


def test_game_check_victory_villagers_win():
    game = GameState(game_id="g1", room_id="r1", seats=6)
    game.players[1] = PlayerState(seat=1, user_id="u1", role=Role.WEREWOLF, alive=False)
    game.players[2] = PlayerState(seat=2, user_id="u2", role=Role.VILLAGER, alive=True)

    # All wolves dead
    winner = game.check_victory()
    assert winner == "villagers"


def test_game_check_victory_ongoing():
    game = GameState(game_id="g1", room_id="r1", seats=6)
    game.players[1] = PlayerState(seat=1, user_id="u1", role=Role.WEREWOLF, alive=True)
    game.players[2] = PlayerState(seat=2, user_id="u2", role=Role.VILLAGER, alive=True)
    game.players[3] = PlayerState(seat=3, user_id="u3", role=Role.VILLAGER, alive=True)

    # Game ongoing
    winner = game.check_victory()
    assert winner is None


def test_tally():
    ballots = {1: 2, 2: 3, 3: 2, 4: None}
    counts = tally(ballots)
    assert counts == {2: 2, 3: 1}


def test_leaders_of():
    counts = {2: 2, 3: 1, 4: 2}
    leaders, top = leaders_of(counts)
    assert top == 2
    assert set(leaders) == {2, 4}


def test_leaders_of_single():
    counts = {2: 3, 3: 1, 4: 2}
    leaders, top = leaders_of(counts)
    assert top == 3
    assert leaders == [2]


def test_leaders_of_empty():
    counts = {}
    leaders, top = leaders_of(counts)
    assert top == 0
    assert leaders == []
