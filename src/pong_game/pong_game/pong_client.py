#!/usr/bin/env python3
"""
ROS 2 Pong Client — Guest / Player 2
Subscribes to /pong/game_state and renders the game display.
Sends paddle input via WebSocket to the server.
Run this on the Guest PC instead of keyboard_controller.
"""
import rclpy
from rclpy.node import Node
from pong_msgs.msg import PongGameState, PongScore
import pygame
import threading
import sys
import os
import tty
import termios
import time
import json
import asyncio
import websockets
from typing import Optional

# Screen
WIDTH, HEIGHT = 1280, 720
FPS = 60

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
    def __init__(self, server_url: str = "ws://localhost:8765"):
        super().__init__('pong_client')

        # Subscribe to game state from Host
        self.sub_state = self.create_subscription(
            PongGameState, '/pong/game_state',
            self.state_callback, 10)

        # Subscribe to score events
        self.sub_score = self.create_subscription(
            PongScore, '/pong/score_event',
            self.score_callback, 10)

        # Optional: Still publish to ROS for backwards compatibility
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
        self.paddle_speed = 0.3
        self.limit        = 2.25

        # WebSocket connection
        self.server_url = server_url
        self.ws_connected = False
        self.ws = None
        self.loop = None

        # Keyboard thread
        self.kb_thread = threading.Thread(
            target=self.read_keyboard, daemon=True)
        self.kb_thread.start()

        # WebSocket thread
        self.ws_thread = threading.Thread(
            target=self.run_websocket_client, daemon=True)
        self.ws_thread.start()

        self.get_logger().info('Pong Client started! You are Player 2 (RIGHT paddle)')
        self.get_logger().info('Controls: W = Up  |  S = Down  |  Q = Quit')
        self.get_logger().info(f'Connecting to WebSocket server at {server_url}...')

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

    def score_callback(self, msg):
        self.get_logger().info(
            f'Score: {msg.score_player1} - {msg.score_player2}  [{msg.event_type}]')

    def publish_paddles(self):
        msg = PongGameState()
        msg.paddle2_y = self.my_paddle_y
        self.pub_paddle.publish(msg)

    def read_keyboard(self):
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                ch = os.read(fd, 1)
                if ch == b'w':
                    self.my_paddle_y = max(
                        self.my_paddle_y - self.paddle_speed, -self.limit)
                    self.send_paddle_command()
                elif ch == b's':
                    self.my_paddle_y = min(
                        self.my_paddle_y + self.paddle_speed, self.limit)
                    self.send_paddle_command()
                elif ch == b'q':
                    break
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

    def send_paddle_command(self):
        """Send paddle position to server via WebSocket"""
        if self.ws_connected and self.ws:
            command = {
                "type": "paddle_move",
                "player": 2,
                "paddle_y": round(self.my_paddle_y, 6)
            }
            try:
                asyncio.run_coroutine_threadsafe(
                    self.ws.send(json.dumps(command)),
                    self.loop)
            except Exception as e:
                self.get_logger().debug(f'Failed to send paddle command: {e}')

    def run_websocket_client(self):
        """Run the WebSocket client in its own event loop"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.websocket_client_main())

    async def websocket_client_main(self):
        """Main WebSocket client coroutine"""
        retry_count = 0
        max_retries = 10
        retry_delay = 2

        while retry_count < max_retries:
            try:
                async with websockets.connect(self.server_url) as websocket:
                    self.ws = websocket
                    self.ws_connected = True
                    self.get_logger().info(f'Connected to WebSocket server at {self.server_url}')
                    retry_count = 0

                    try:
                        async for message in websocket:
                            pass
                    except websockets.exceptions.ConnectionClosed:
                        self.get_logger().warning('WebSocket connection closed by server')
                    finally:
                        self.ws_connected = False
                        self.ws = None

            except Exception as e:
                retry_count += 1
                self.get_logger().warning(
                    f'WebSocket connection attempt {retry_count}/{max_retries} failed: {e}')

                if retry_count < max_retries:
                    await asyncio.sleep(retry_delay)
                else:
                    self.get_logger().error('Max WebSocket connection retries reached')
                    break


def draw_court(screen):
    screen.fill((10, 80, 40))
    pygame.draw.rect(screen, WHITE, (20, 20, WIDTH-40, HEIGHT-40), 6, border_radius=6)
    dash_h, gap = 20, 18
    x = WIDTH // 2
    y = 30
    while y < HEIGHT - 30:
        pygame.draw.rect(screen, WHITE, (x-2, y, 4, dash_h))
        y += dash_h + gap


def draw_game(screen, node, fonts):
    draw_court(screen)

    # Paddles
    pygame.draw.rect(screen, GREEN,
        (LEFT_MARGIN, int(node.paddle1_y) - PADDLE_H//2, PADDLE_W, PADDLE_H),
        border_radius=6)
    pygame.draw.rect(screen, RED,
        (WIDTH - LEFT_MARGIN - PADDLE_W, int(node.paddle2_y) - PADDLE_H//2,
         PADDLE_W, PADDLE_H), border_radius=6)

    # Ball
    pygame.draw.circle(screen, CYAN,
        (int(node.ball_x), int(node.ball_y)), BALL_SIZE)
    pygame.draw.circle(screen, WHITE,
        (int(node.ball_x), int(node.ball_y)), BALL_SIZE - 4)

    # Score
    s1 = fonts['big'].render(str(node.score1), True, GREEN)
    s2 = fonts['big'].render(str(node.score2), True, RED)
    screen.blit(s1, (WIDTH//2 - 80, 15))
    screen.blit(s2, (WIDTH//2 + 45, 15))

    # Status overlay
    if node.game_status == 0:
        txt = fonts['medium'].render('Waiting for Host...', True, YELLOW)
        screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - 20))
    elif node.game_status == 2:
        txt = fonts['big'].render('PLAYER 1 WINS!', True, GREEN)
        screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - 40))
    elif node.game_status == 3:
        txt = fonts['big'].render('PLAYER 2 WINS!', True, RED)
        screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - 40))

    # You are Player 2 label
    p2_label = fonts['tiny'].render('YOU  (Player 2)', True, RED)
    screen.blit(p2_label, (WIDTH - LEFT_MARGIN - PADDLE_W - p2_label.get_width() - 10,
                            int(node.paddle2_y) - 20))

    # Controls hint
    hint = fonts['tiny'].render('W = Up   S = Down   Q = Quit', True, LIGHT_GRAY)
    screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT - 30))

    pygame.display.flip()


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
    
    # Get server URL from environment or command line
    server_url = os.environ.get('PONG_SERVER_URL', "ws://localhost:8765")
    if len(sys.argv) > 1:
        server_url = sys.argv[1]
    
    node = PongClient(server_url=server_url)

    ros_thread = threading.Thread(
        target=rclpy.spin, args=(node,), daemon=True)
    ros_thread.start()

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('ROS 2 Pong — Guest (Player 2)')
    clock = pygame.time.Clock()

    fonts = {
        'big':    pygame.font.Font(None, 70),
        'medium': pygame.font.Font(None, 48),
        'small':  pygame.font.Font(None, 34),
        'tiny':   pygame.font.Font(None, 26),
    }

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        if node.game_status == 1:
            draw_game(screen, node, fonts)
        else:
            draw_waiting(screen, fonts)

        clock.tick(FPS)

    pygame.quit()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()