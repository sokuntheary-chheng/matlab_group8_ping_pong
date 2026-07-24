def update_client_paddle_position(current_y, key_up, key_down, speed, limit):
    """Move the client paddle with the same semantics as local play.

    The client uses W for moving upward and S for moving downward, matching
    the host-side Player 1 controls.
    """
    if key_up and not key_down:
        return round(max(current_y - speed, -limit), 6)
    if key_down and not key_up:
        return round(min(current_y + speed, limit), 6)
    return round(current_y, 6)
