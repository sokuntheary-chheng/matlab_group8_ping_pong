#!/usr/bin/env python3
"""
ROS 2 Pong Client — Guest / Player 2
Subscribes to /pong/game_state and renders the game display.
Also publishes paddle input via /pong/paddle_input.
Run this on the Guest PC instead of keyboard_controller.
"""
import pygame
import threading
import time

from pong_game.network_controls import update_client_paddle_position

try:
    import rclpy
    from rclpy.node import Node
    from pong_msgs.msg import PongGameState, PongScore
except Exception:  # pragma: no cover - exercised in minimal test environments
    rclpy = None
    Node = object
    PongGameState = None
    PongScore = None

from pong_game import settings as settings_mod

try:
    from pong_game import pygame_pong as host_ui
except Exception:  # pragma: no cover - fallback when ROS module is unavailable
    host_ui = None

# Screen
WIDTH, HEIGHT = (1280, 720)
FPS = 60
if host_ui is not None:
    WIDTH, HEIGHT = host_ui.WIDTH, host_ui.HEIGHT
    FPS = host_ui.FPS

# Colors
BLACK      = (0, 0, 0)
WHITE      = (255, 255, 255)
GREEN      = (0, 255, 100)
RED        = (255, 60, 60)
CYAN       = (0, 220, 220)
DARK_GRAY  = (20, 20, 30)
YELLOW     = (255, 220, 0)
LIGHT_GRAY = (80, 80, 80)
BLUE       = (60, 140, 255)

# Game constants
PADDLE_W  = 14
PADDLE_H  = 90
BALL_SIZE = 11
LEFT_MARGIN = 50


class PongClient(Node):
    def __init__(self):
        if Node is object:
            raise RuntimeError('rclpy is required to run the pong client')
        super().__init__('pong_client')

        # Subscribe to game state from Host
        self.sub_state = self.create_subscription(
            PongGameState, '/pong/game_state',
            self.state_callback, 10)

        # Subscribe to score events
        self.sub_score = self.create_subscription(
            PongScore, '/pong/score_event',
            self.score_callback, 10)

        # Publish paddle input to Host
        self.pub_paddle = self.create_publisher(
            PongGameState, '/pong/paddle_input', 10)

        self.create_timer(0.05, self.publish_paddles)

        # Game state received from host
        self.ball_x      = float(WIDTH // 2)
        self.ball_y      = float(HEIGHT // 2)
        self.ball_vx     = 0.0
        self.ball_vy     = 0.0
        self.paddle1_y   = float(HEIGHT // 2)
        self.paddle2_y   = float(HEIGHT // 2)
        self.score1      = 0
        self.score2      = 0
        self.game_status = 0

        # Local paddle control (normalized -2.25 to 2.25)
        self.my_paddle_y  = 0.0
        self.paddle_speed = 0.3  # will be updated dynamically based on ball speed
        self.limit        = 2.25
        self.speed_mult   = 1.0
        self._last_ball_speed = 1.0  # track previous ball speed to detect changes

        # Countdown timer state
        self.countdown_active = False
        self.countdown_time = 0.0
        self.countdown_max = 3.0
        self.last_scorer = 0

        self.get_logger().info('Pong Client started! You are Player 2 (RIGHT paddle)')
        self.get_logger().info('Controls: W = Up  |  S = Down  |  Q = Quit')

    def state_callback(self, msg):
        self.ball_x      = msg.ball_x
        self.ball_y      = msg.ball_y
        self.ball_vx     = msg.ball_vel_x
        self.ball_vy     = msg.ball_vel_y
        self.paddle1_y   = msg.paddle1_y
        self.paddle2_y   = msg.paddle2_y
        self.score1      = msg.score_player1
        self.score2      = msg.score_player2
        self.game_status = msg.game_status

        # Update paddle speed dynamically based on ball velocity
        # Use same formula as HOST: paddle_speed = ball_speed * 0.88
        ball_speed = max(abs(self.ball_vx), abs(self.ball_vy), 1.0)
        self.paddle_speed = ball_speed * 0.88
        self.paddle_speed = min(self.paddle_speed, ball_speed * 0.95)
        self.paddle_speed = max(3.0, min(self.paddle_speed, 20.0))

        # Update speed_mult to track ball acceleration
        # Match HOST behavior: speed_mult increases each time ball is hit
        if ball_speed > self._last_ball_speed:
            inc_pct = (ball_speed - self._last_ball_speed) / max(1.0, self._last_ball_speed)
            self.speed_mult = min(self.speed_mult + inc_pct, 5.0)
        self._last_ball_speed = ball_speed

    def score_callback(self, msg):
        self.get_logger().info(
            f'Score: {msg.score_player1} - {msg.score_player2}  [{msg.event_type}]')

    def start_countdown(self, scorer):
        self.countdown_active = True
        self.countdown_time = 0.0
        self.last_scorer = scorer

    def update_countdown(self, dt):
        if not self.countdown_active:
            return False

        self.countdown_time += dt
        if self.countdown_time >= self.countdown_max:
            self.countdown_active = False
            return True
        return False

    def publish_paddles(self):
        # Publish normalized paddle input for Player 2 (paddle2_y).
        # Also include paddle1_y (unused by client) to keep message fields consistent.
        msg = PongGameState()
        msg.paddle1_y = 0.0
        msg.paddle2_y = float(self.my_paddle_y)
        self.pub_paddle.publish(msg)

def draw_game(screen, node, fonts, particles=None, trail=None, settings_dict=None, clock=None):
    """Render the client UI using the same host renderer for visual parity."""
    if host_ui is not None:
        host_ui.draw_game(
            screen,
            node,
            fonts,
            mode=3,
            particles=particles if particles is not None else [],
            trail=trail if trail is not None else [],
            settings_dict=settings_dict if settings_dict is not None else {},
            clock=clock,
        )
        return

    screen.fill(DARK_GRAY)
    pygame.draw.rect(screen, WHITE, (20, 20, WIDTH - 40, HEIGHT - 40), 6, border_radius=6)
    txt = fonts['medium'].render('Waiting for host renderer...', True, YELLOW)
    screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 20))
    pygame.display.flip()


def update_client_paddle_from_keys(node, pressed_keys):
    """Synchronize client paddle movement with the host-side rendered paddle.

    pressed_keys may be either:
    - a set of key constants (e.g. {pygame.K_w}) maintained by the event loop, or
    - the sequence returned by pygame.key.get_pressed() where indexes are key constants.
    This helper accepts both to be robust across different calling code / tests.
    """
    def _is_down(collection, key):
        try:
            # Most common case: a set containing key ints
            return key in collection
        except Exception:
            try:
                # pygame.key.get_pressed() returns a sequence of bools
                return bool(collection[key])
            except Exception:
                return False

    key_up = _is_down(pressed_keys, pygame.K_w)
    key_down = _is_down(pressed_keys, pygame.K_s)

    # Convert pixel-based paddle_speed to normalized units
    # norm_to_pixel = (HEIGHT // 2 - PADDLE_H // 2) / 2.25
    half = PADDLE_H // 2
    norm_to_pixel = (HEIGHT // 2 - half) / 2.25
    norm_speed = node.paddle_speed / norm_to_pixel

    node.my_paddle_y = update_client_paddle_position(
        node.my_paddle_y,
        key_up,
        key_down,
        norm_speed,
        node.limit,
    )

    node.paddle2_y = float((HEIGHT // 2) + node.my_paddle_y * ((HEIGHT // 2 - half) / 2.25))
    node.paddle2_y = max(half, min(node.paddle2_y, HEIGHT - half))
    return True


def handle_pygame_input(event, node):
    """Handle keyboard input from pygame events."""
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_q:
            return False
    return True


def draw_waiting(screen, fonts):
    screen.fill(DARK_GRAY)
    pygame.draw.rect(screen, BLUE, (0, 0, WIDTH, HEIGHT), 3)
    title = fonts['big'].render('ROS 2 PONG — Guest Client', True, CYAN)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 80))
    lines = [
        ('Waiting for Host to start the game...', YELLOW),
        ('', WHITE),
        ('Make sure Host PC has launched:', WHITE),
        ('ros2 launch pong_game pong.launch.py', GREEN),
        ('', WHITE),
        ('And selected  "Across 2 PCs"  then pressed SPACE', WHITE),
        ('', WHITE),
        ('Your controls:', CYAN),
        ('W = Move Up   |   S = Move Down   |   Q = Quit', WHITE),
        ('', WHITE),
        ('You are:  Player 2  (RIGHT paddle — RED)', RED),
    ]
    y = 180
    for line, color in lines:
        if line == '':
            y += 15
            continue
        txt = fonts['small'].render(line, True, color)
        screen.blit(txt, (WIDTH//2 - txt.get_width()//2, y))
        y += 40
    pygame.display.flip()


def main(args=None):
    rclpy.init(args=args)
    node = PongClient()

    ros_thread = threading.Thread(
        target=rclpy.spin, args=(node,), daemon=True)
    ros_thread.start()

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('ROS 2 Pong — Group 8')
    clock = pygame.time.Clock()

    settings = settings_mod.load_settings()
    fonts = {
        'title':  pygame.font.Font(None, 95),
        'big':    pygame.font.Font(None, 70),
        'medium': pygame.font.Font(None, 48),
        'small':  pygame.font.Font(None, 34),
        'tiny':   pygame.font.Font(None, 26),
    }

    particles = []
    trail = []

    pressed_keys = set()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                pressed_keys.add(event.key)
                if event.key == pygame.K_ESCAPE:
                    running = False
                else:
                    running = handle_pygame_input(event, node)
            elif event.type == pygame.KEYUP:
                pressed_keys.discard(event.key)

        if node.game_status == 1:
            update_client_paddle_from_keys(node, pressed_keys)

        draw_game(screen, node, fonts, particles, trail, settings, clock)
        clock.tick(FPS)

    pygame.quit()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()