from pong_game.network_controls import update_client_paddle_position


def test_w_moves_paddle_up():
    assert update_client_paddle_position(0.2, True, False, 0.3, 2.25) == -0.1


def test_s_moves_paddle_down():
    assert update_client_paddle_position(0.2, False, True, 0.3, 2.25) == 0.5


def test_no_input_keeps_position():
    assert update_client_paddle_position(0.2, False, False, 0.3, 2.25) == 0.2
