import pygame
import types

from pong_game import pong_client
from pong_game.network_controls import update_client_paddle_position
from pong_game.settings import get_winning_score


def test_w_moves_paddle_up():
    assert update_client_paddle_position(0.2, True, False, 0.3, 2.25) == -0.1


def test_s_moves_paddle_down():
    assert update_client_paddle_position(0.2, False, True, 0.3, 2.25) == 0.5


def test_no_key_keeps_position():
    assert update_client_paddle_position(0.2, False, False, 0.3, 2.25) == 0.2


def test_winning_score_uses_saved_settings():
    settings = {"gameplay": {"winning_score": 10}}
    assert get_winning_score(settings, 5) == 10


def test_client_key_input_updates_local_paddle_and_display():
    node = types.SimpleNamespace(my_paddle_y=0.2, paddle_speed=0.3, limit=2.25, paddle2_y=0.0)
    pong_client.update_client_paddle_from_keys(node, {pygame.K_w})
    assert node.my_paddle_y == -0.1
    assert node.paddle2_y < 360.0

    pong_client.update_client_paddle_from_keys(node, {pygame.K_s})
    assert node.my_paddle_y == 0.2
    assert node.paddle2_y > 360.0
