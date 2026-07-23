def update_client_paddle_position(current_y, key_up, key_down, speed, limit):
    """Move the client paddle with the same semantics as local play.

    Up input decreases the paddle position (toward the top of the screen)
    and down input increases it (toward the bottom), matching the
    single-player and two-player controls.
    """
    if key_up and not key_down:
        return round(max(current_y - speed, -limit), 6)
    if key_down and not key_up:
        return round(min(current_y + speed, limit), 6)
    return round(current_y, 6)
