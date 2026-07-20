import rclpy
from rclpy.node import Node
from pong_msgs.msg import PongGameState, PongScore
import pygame
import sys
import threading
import random
import socket
import numpy as np
import time
from pong_game.sound_gen import load_sounds, start_bgm, start_home_bgm, stop_bgm, _SOUND_CACHE
from pong_game import settings as settings_mod

# Screen
WIDTH, HEIGHT = 1280, 720
FPS = 60

# Scaling reference (original used 900x600)
_SCALE = WIDTH / 900.0

# Colors
BLACK     = (0, 0, 0)
WHITE     = (255, 255, 255)
GREEN     = (0, 255, 100)
RED       = (255, 60, 60)
BLUE      = (60, 140, 255)
YELLOW    = (255, 220, 0)
GRAY      = (40, 40, 40)
DARK_GRAY = (20, 20, 30)
CYAN      = (0, 220, 220)
ORANGE    = (255, 160, 0)
PURPLE    = (160, 60, 255)
LIGHT_GRAY= (80, 80, 80)

# Game constants
PADDLE_W  = int(14 * _SCALE)
PADDLE_H  = int(90 * _SCALE)
BALL_SIZE = int(11 * _SCALE)
WIN_SCORE = 5
AI_SPEED  = 4
LEFT_MARGIN = int(50 * _SCALE)

# ─── Button ──────────────────────────────────────────────
class Button:
    def __init__(self, x, y, w, h, text, color, hover, text_color=WHITE):
        self.rect       = pygame.Rect(x, y, w, h)
        self.text       = text
        self.color      = color
        self.hover      = hover
        self.text_color = text_color

    def draw(self, screen, font):
        c = self.hover if self.rect.collidepoint(pygame.mouse.get_pos()) else self.color
        pygame.draw.rect(screen, c, self.rect, border_radius=12)
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=12)
        t = font.render(self.text, True, self.text_color)
        screen.blit(t, (self.rect.centerx - t.get_width()//2,
                        self.rect.centery - t.get_height()//2))

    def is_clicked(self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN and
                self.rect.collidepoint(event.pos))

# ─── Particle ────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, color):
        self.x     = x
        self.y     = y
        self.vx    = random.uniform(-3, 3)
        self.vy    = random.uniform(-4, 1)
        self.life  = 1.0
        self.color = color
        self.size  = random.randint(3, 7)

    def update(self):
        self.x    += self.vx
        self.y    += self.vy
        self.vy   += 0.2
        self.life -= 0.05

    def draw(self, screen):
        if self.life > 0:
            alpha = int(self.life * 255)
            c = (*self.color[:3], alpha)
            s = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
            pygame.draw.circle(s, c, (self.size, self.size), self.size)
            screen.blit(s, (int(self.x)-self.size, int(self.y)-self.size))

# ─── ROS2 Node ───────────────────────────────────────────
class PongNode(Node):
    def __init__(self, settings_dict=None):
        super().__init__('pygame_pong')
        self.state_pub = self.create_publisher(      # publisher for game state updates
            PongGameState, '/pong/game_state', 10)
        self.score_pub = self.create_publisher(      # publisher for score events (scores, wins)
            PongScore, '/pong/score_event', 10)
        self.paddle_sub = self.create_subscription(  # subscriber for network P2 paddle input
            PongGameState, '/pong/paddle_input', self.paddle_callback, 10)
        self.create_timer(0.05, self.publish_state)
        # calls publish_state() every 0.05 seconds = 20 times per second (20Hz)
        self.get_logger().info('ROS2 Pong Node started!')
        self._network_mode = False  # set True when in Across 2 PCs mode

        self.settings = settings_dict or {}

        # Game state
        self.ball_x    = float(WIDTH // 2)
        self.ball_y    = float(HEIGHT // 2)
        self.ball_vx   = 0.0
        self.ball_vy   = 0.0
        self.paddle1_y = float(HEIGHT // 2)
        self.paddle2_y = float(HEIGHT // 2)
        self.score1    = 0
        self.score2    = 0
        self.game_status = 1
        self.speed_mult  = 1.0

        # Countdown timer state
        self.countdown_active = False
        self.countdown_time = 0.0
        self.countdown_max = 3.0
        self.last_scorer = 0  # 1 or 2

        # Guest / partner mode (this PC joins as Player 2 over the network)
        self.is_guest          = False
        self.guest_state_sub   = None
        self.guest_score_sub   = None
        self.guest_paddle_pub  = None
        self.guest_ball_x      = float(WIDTH // 2)
        self.guest_ball_y      = float(HEIGHT // 2)
        self.guest_paddle1_y   = float(HEIGHT // 2)
        self.guest_paddle2_y   = float(HEIGHT // 2)
        self.guest_score1      = 0
        self.guest_score2      = 0
        self.guest_game_status = 0  # 0 = waiting for host
        self.guest_my_paddle_y = 0.0  # normalized -2.25..2.25, sent to host

    def enable_guest_mode(self):
        """Turn this instance into a network Guest (Player 2) instead of Host."""
        if self.is_guest:
            return
        self.is_guest = True
        self.guest_ball_x      = float(WIDTH // 2)
        self.guest_ball_y      = float(HEIGHT // 2)
        self.guest_paddle1_y   = float(HEIGHT // 2)
        self.guest_paddle2_y   = float(HEIGHT // 2)
        self.guest_score1      = 0
        self.guest_score2      = 0
        self.guest_game_status = 0
        self.guest_my_paddle_y = 0.0
        self.guest_state_sub = self.create_subscription(
            PongGameState, '/pong/game_state', self.guest_state_callback, 10)
        self.guest_score_sub = self.create_subscription(
            PongScore, '/pong/score_event', self.guest_score_callback, 10)
        self.guest_paddle_pub = self.create_publisher(
            PongGameState, '/pong/paddle_input', 10)
        self.create_timer(0.05, self.publish_guest_paddle)
        self.get_logger().info('Guest mode enabled — you are Player 2 (RIGHT paddle)')

    def guest_state_callback(self, msg):
        self.guest_ball_x      = msg.ball_x
        self.guest_ball_y      = msg.ball_y
        self.guest_paddle1_y   = msg.paddle1_y
        self.guest_paddle2_y   = msg.paddle2_y
        self.guest_score1      = msg.score_player1
        self.guest_score2      = msg.score_player2
        self.guest_game_status = msg.game_status

    def guest_score_callback(self, msg):
        self.get_logger().info(
            f'[Guest] Score: {msg.score_player1}-{msg.score_player2}  [{msg.event_type}]')

    def publish_guest_paddle(self):
        if not self.is_guest or self.guest_paddle_pub is None:
            return
        msg = PongGameState()
        msg.paddle2_y = float(self.guest_my_paddle_y)
        self.guest_paddle_pub.publish(msg)

    def reset_game(self):
        self.paddle1_y   = float(HEIGHT // 2)
        self.paddle2_y   = float(HEIGHT // 2)
        self.score1      = 0
        self.score2      = 0
        self.game_status = 1
        self.speed_mult  = 1.0
        self.publish_score_event(0, 'start', '')
        self.start_countdown(0)

    def start_countdown(self, scorer):
        self.countdown_active = True
        self.countdown_time = 0.0
        self.last_scorer = scorer
        self.ball_x = float(WIDTH // 2)
        self.ball_y = float(HEIGHT // 2)
        self.ball_vx = 0.0
        self.ball_vy = 0.0
        if scorer != 0:
            self.speed_mult = 1.0

    def update_countdown(self, dt):
        if not self.countdown_active:
            return False

        self.countdown_time += dt
        if self.countdown_time >= self.countdown_max:
            base_speed = float(self.settings.get('gameplay', {}).get('ball_start_speed', 4.0))
            if self.last_scorer == 0:
                self.ball_vx = base_speed * random.choice([-1, 1])
            elif self.last_scorer == 1:
                self.ball_vx = base_speed
            else:
                self.ball_vx = -base_speed
            self.ball_vy = random.uniform(-2.0, 2.0)
            self.countdown_active = False
            return True
        return False

    def publish_score_event(self, player, event_type, winner):
        msg              = PongScore()
        msg.player_scored  = int(player)
        msg.score_player1  = int(self.score1)
        msg.score_player2  = int(self.score2)
        msg.event_type     = str(event_type)
        msg.winner         = str(winner)
        self.score_pub.publish(msg)
        self.get_logger().info(
            f'[ScoreEvent] {event_type} | {self.score1}-{self.score2}')

    def publish_state(self):
        msg                = PongGameState()
        msg.ball_x         = float(self.ball_x)
        msg.ball_y         = float(self.ball_y)
        msg.ball_vel_x     = float(self.ball_vx)
        msg.ball_vel_y     = float(self.ball_vy)
        msg.paddle1_y      = float(self.paddle1_y)
        msg.paddle2_y      = float(self.paddle2_y)
        msg.score_player1  = int(self.score1)
        msg.score_player2  = int(self.score2)
        msg.game_status    = int(self.game_status)
        self.state_pub.publish(msg)

    def paddle_callback(self, msg):
        """Receive paddle positions from keyboard_controller (network/Across 2 PCs mode)"""
        if self._network_mode and self.game_status == 1 and not self.countdown_active:
            half = PADDLE_H // 2
            self.paddle2_y = float(
                (HEIGHT // 2) + msg.paddle2_y * ((HEIGHT // 2 - half) / 2.25)
            )
            self.paddle2_y = max(half, min(self.paddle2_y, HEIGHT - half))

# ─── Drawing helpers ─────────────────────────────────────
def draw_bg(screen, settings_dict):
    if settings_dict.get('display', {}).get('court', True):
        court_color = (10, 80, 40) if not settings_dict.get('accessibility', {}).get('colorblind', False) else (10, 40, 80)
        screen.fill(court_color)
        shadow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 60), (10, 10, WIDTH-20, HEIGHT-20), border_radius=12)
        screen.blit(shadow, (0, 0))
        boundary_thick = int(6 * _SCALE)
        pygame.draw.rect(screen, WHITE, (20, 20, WIDTH-40, HEIGHT-40), boundary_thick, border_radius=6)
        dash_h = int(20 * _SCALE)
        gap = int(18 * _SCALE)
        x = WIDTH//2
        y = 30
        while y < HEIGHT-30:
            pygame.draw.rect(screen, WHITE, (x-2, y, 4, dash_h))
            y += dash_h + gap
        box_w = int((WIDTH-200)//2)
        box_h = int((HEIGHT-120))
        pygame.draw.rect(screen, WHITE, (80, 60, box_w, box_h), 2)
        pygame.draw.rect(screen, WHITE, (WIDTH-80-box_w, 60, box_w, box_h), 2)
        bleacher_color = (40, 40, 60)
        pygame.draw.rect(screen, bleacher_color, (0, 0, WIDTH, 24))
        pygame.draw.rect(screen, bleacher_color, (0, HEIGHT-24, WIDTH, 24))
    else:
        screen.fill(DARK_GRAY)

def draw_home(screen, buttons, fonts, particles, help_btn, settings_btn):
    screen.fill(DARK_GRAY)
    for p in particles:
        p.update()
        p.draw(screen)
    particles[:] = [p for p in particles if p.life > 0]
    if random.random() < 0.3:
        particles.append(Particle(
            random.randint(0, WIDTH),
            random.randint(0, HEIGHT),
            random.choice([CYAN, BLUE, GREEN, PURPLE])))

    title = fonts['title'].render('ROS 2 PONG', True, CYAN)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))

    sub = fonts['medium'].render('Group 8 | ITC Year 2 | Semester 2', True, LIGHT_GRAY)
    screen.blit(sub, (WIDTH//2 - sub.get_width()//2, 145))

    for btn in buttons:
        btn.draw(screen, fonts['small'])

    help_btn.draw(screen, fonts['tiny'])
    settings_btn.draw(screen, fonts['tiny'])

    footer = fonts['tiny'].render(
        'ROS 2 Jazzy | Custom Messages | pong_msgs/PongGameState',
        True, LIGHT_GRAY)
    screen.blit(footer, (WIDTH//2 - footer.get_width()//2, HEIGHT-30))
    pygame.draw.rect(screen, BLUE, (0, 0, WIDTH, HEIGHT), 3)
    pygame.display.flip()

def draw_countdown(screen, node, fonts):
    remaining = node.countdown_max - node.countdown_time
    countdown_num = max(0, int(remaining) + 1)
    if countdown_num > 0:
        if countdown_num == 3:
            color = RED
        elif countdown_num == 2:
            color = YELLOW
        else:
            color = GREEN
        txt = fonts['big'].render(str(countdown_num), True, color)
        glow = pygame.Surface((txt.get_width() + 40, txt.get_height() + 40), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*color, 80), (txt.get_width()//2 + 20, txt.get_height()//2 + 20), txt.get_height()//2 + 15)
        screen.blit(glow, (WIDTH//2 - glow.get_width()//2, HEIGHT//2 - glow.get_height()//2))
        screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - txt.get_height()//2))

def draw_game(screen, node, fonts, mode, particles, trail, settings_dict, clock=None):
    draw_bg(screen, settings_dict)

    if settings_dict.get('display', {}).get('effects', True):
        for i, (tx, ty) in enumerate(trail):
            alpha = int((i / len(trail)) * 120) if trail else 0
            s = pygame.Surface((BALL_SIZE*2, BALL_SIZE*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (0, 220, 220, alpha), (BALL_SIZE, BALL_SIZE), BALL_SIZE)
            screen.blit(s, (int(tx)-BALL_SIZE, int(ty)-BALL_SIZE))

    if settings_dict.get('display', {}).get('effects', True):
        for p in particles:
            p.update()
            p.draw(screen)
        particles[:] = [p for p in particles if p.life > 0]

    if settings_dict.get('accessibility', {}).get('high_contrast', False):
        p1_color = WHITE
        p2_color = WHITE
    else:
        p1_color = GREEN
        p2_color = RED

    pygame.draw.rect(screen, (0, 100, 50),
        (LEFT_MARGIN-2, int(node.paddle1_y)-PADDLE_H//2-2, PADDLE_W+4, PADDLE_H+4),
        border_radius=8)
    pygame.draw.rect(screen, p1_color,
        (LEFT_MARGIN, int(node.paddle1_y)-PADDLE_H//2, PADDLE_W, PADDLE_H),
        border_radius=6)

    pygame.draw.rect(screen, (100, 20, 20),
        (WIDTH-LEFT_MARGIN-PADDLE_W-2, int(node.paddle2_y)-PADDLE_H//2-2,
         PADDLE_W+4, PADDLE_H+4), border_radius=8)
    pygame.draw.rect(screen, p2_color,
        (WIDTH-LEFT_MARGIN-PADDLE_W, int(node.paddle2_y)-PADDLE_H//2,
         PADDLE_W, PADDLE_H), border_radius=6)

    ball_col = WHITE if settings_dict.get('accessibility', {}).get('high_contrast', False) else CYAN
    pygame.draw.circle(screen, ball_col,
        (int(node.ball_x), int(node.ball_y)), BALL_SIZE)
    pygame.draw.circle(screen, WHITE,
        (int(node.ball_x), int(node.ball_y)), BALL_SIZE-4)

    s1 = fonts['big'].render(str(node.score1), True, GREEN)
    s2 = fonts['big'].render(str(node.score2), True, RED)
    screen.blit(s1, (WIDTH//2 - 80, 15))
    screen.blit(s2, (WIDTH//2 + 45, 15))

    spd = fonts['tiny'].render(
        f'Speed: {node.speed_mult:.1f}x', True, YELLOW)
    screen.blit(spd, (WIDTH//2 - spd.get_width()//2, 75))

    esc = fonts['tiny'].render('ESC=Home  R=Restart', True, LIGHT_GRAY)
    screen.blit(esc, (WIDTH//2 - esc.get_width()//2, HEIGHT-30))
    if settings_dict.get('display', {}).get('show_fps', False):
        fps_surf = fonts['tiny'].render(
            f'FPS: {int(clock.get_fps())}', True, YELLOW)
        screen.blit(fps_surf, (10, 10))

    if node.countdown_active:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        screen.blit(overlay, (0, 0))
        draw_countdown(screen, node, fonts)

    if node.game_status in (2, 3):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        if node.game_status == 2:
            winner_txt = 'YOU WIN!' if mode == 1 else 'PLAYER 1 WINS!'
            color = GREEN
        else:
            winner_txt = 'AI WINS!' if mode == 1 else 'PLAYER 2 WINS!'
            color = RED

        wtxt = fonts['big'].render(winner_txt, True, color)
        screen.blit(wtxt, (WIDTH//2 - wtxt.get_width()//2, HEIGHT//2 - 60))

        hint = fonts['small'].render('R = Restart   ESC = Home', True, WHITE)
        screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT//2 + 20))

    pygame.display.flip()

def draw_network(screen, fonts, back_btn):
    screen.fill(DARK_GRAY)
    pygame.draw.rect(screen, BLUE, (0, 0, WIDTH, HEIGHT), 3)

    try:
        host_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        host_ip = 'Run ipconfig in PowerShell'

    title = fonts['medium'].render('Network Multiplayer — Across 2 PCs', True, CYAN)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 30))

    subtitle = fonts['tiny'].render('Both PCs must be on the same WiFi or hotspot', True, YELLOW)
    screen.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, 78))
    pygame.draw.line(screen, LIGHT_GRAY, (60, 110), (WIDTH - 60, 110), 1)

    label = fonts['small'].render('Your IP Address:', True, WHITE)
    screen.blit(label, (WIDTH//2 - label.get_width()//2, 135))

    ip_box = pygame.Rect(WIDTH//2 - 220, 175, 440, 54)
    pygame.draw.rect(screen, (20, 40, 60), ip_box, border_radius=12)
    pygame.draw.rect(screen, CYAN, ip_box, 3, border_radius=12)
    ip_text = fonts['small'].render(host_ip, True, WHITE)
    screen.blit(ip_text, (ip_box.centerx - ip_text.get_width()//2,
                          ip_box.centery - ip_text.get_height()//2))

    note = fonts['tiny'].render('Share this IP with your partner', True, LIGHT_GRAY)
    screen.blit(note, (WIDTH//2 - note.get_width()//2, 245))

    host_btn = Button(WIDTH//2 - 310, HEIGHT//2 - 30, 620, 60,
                      '▶  Start as HOST  (You = Player 1 Left Paddle)',
                      (30, 120, 30), (50, 180, 50))
    host_btn.draw(screen, fonts['small'])

    join_btn = Button(WIDTH//2 - 310, HEIGHT//2 + 46, 620, 60,
                      '🤝  Join as PARTNER  (You = Player 2 Right Paddle)',
                      (30, 60, 120), (50, 90, 180))
    join_btn.draw(screen, fonts['small'])

    back_btn.rect = pygame.Rect(WIDTH - 210, HEIGHT - 70, 190, 50)
    back_btn.color = (120, 40, 40)
    back_btn.hover = (180, 60, 60)
    back_btn.text = ' Back to Home'
    back_btn.draw(screen, fonts['small'])

    hint1 = fonts['tiny'].render('Partner runs: python3 ~/pong_controller.py <YOUR_IP>', True, WHITE)
    screen.blit(hint1, (WIDTH//2 - hint1.get_width()//2, HEIGHT - 78))
    hint2 = fonts['tiny'].render('Press SPACE or click Start as HOST to begin', True, WHITE)
    screen.blit(hint2, (WIDTH//2 - hint2.get_width()//2, HEIGHT - 48))

    pygame.display.flip()

    keys = pygame.key.get_pressed()
    if keys[pygame.K_SPACE]:
        return 'start'
    if keys[pygame.K_ESCAPE]:
        return 'back'

    if pygame.mouse.get_pressed()[0]:
        mx, my = pygame.mouse.get_pos()
        if host_btn.rect.collidepoint(mx, my):
            return 'start'
        if join_btn.rect.collidepoint(mx, my):
            return 'join'
        if back_btn.rect.collidepoint(mx, my):
            return 'back'

    return None

def draw_guest(screen, node, fonts):
    """Render the game while this PC is acting as network Guest (Player 2)."""
    if node.guest_game_status == 0:
        screen.fill(DARK_GRAY)
        pygame.draw.rect(screen, BLUE, (0, 0, WIDTH, HEIGHT), 3)
        title = fonts['big'].render('Waiting for Host…', True, YELLOW)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 80))
        sub = fonts['small'].render(
            'Make sure the Host has clicked "Start as HOST"', True, WHITE)
        screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 - 10))
        hint = fonts['tiny'].render('W = Up   S = Down   ESC = Back to Home', True, LIGHT_GRAY)
        screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT - 40))
        pygame.display.flip()
        return

    screen.fill((10, 80, 40))
    pygame.draw.rect(screen, WHITE, (20, 20, WIDTH-40, HEIGHT-40), 6, border_radius=6)
    dash_h, gap = 20, 18
    x = WIDTH // 2
    y = 30
    while y < HEIGHT - 30:
        pygame.draw.rect(screen, WHITE, (x-2, y, 4, dash_h))
        y += dash_h + gap

    pygame.draw.rect(screen, GREEN,
        (LEFT_MARGIN, int(node.guest_paddle1_y) - PADDLE_H//2, PADDLE_W, PADDLE_H),
        border_radius=6)
    pygame.draw.rect(screen, RED,
        (WIDTH - LEFT_MARGIN - PADDLE_W, int(node.guest_paddle2_y) - PADDLE_H//2,
         PADDLE_W, PADDLE_H), border_radius=6)

    pygame.draw.circle(screen, CYAN,
        (int(node.guest_ball_x), int(node.guest_ball_y)), BALL_SIZE)
    pygame.draw.circle(screen, WHITE,
        (int(node.guest_ball_x), int(node.guest_ball_y)), BALL_SIZE - 4)

    s1 = fonts['big'].render(str(node.guest_score1), True, GREEN)
    s2 = fonts['big'].render(str(node.guest_score2), True, RED)
    screen.blit(s1, (WIDTH//2 - 80, 15))
    screen.blit(s2, (WIDTH//2 + 45, 15))

    if node.guest_game_status == 2:
        txt = fonts['big'].render('PLAYER 1 WINS!', True, GREEN)
        screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - 40))
    elif node.guest_game_status == 3:
        txt = fonts['big'].render('PLAYER 2 WINS!', True, RED)
        screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - 40))

    p2_label = fonts['tiny'].render('YOU  (Player 2)', True, RED)
    screen.blit(p2_label, (WIDTH - LEFT_MARGIN - PADDLE_W - p2_label.get_width() - 10,
                            int(node.guest_paddle2_y) - 20))

    hint = fonts['tiny'].render('W = Up   S = Down   ESC = Back to Home', True, LIGHT_GRAY)
    screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT - 30))

    pygame.display.flip()

def draw_settings(screen, fonts, settings_dict, clock):
    running = True
    current_section = 0
    sections = ['GAMEPLAY', 'AUDIO', 'DISPLAY', 'CONTROLS', 'ACCESSIBILITY']
    _click = [False]
    _click_pos = [-1, -1]

    back_btn = Button(WIDTH - 210, HEIGHT - 70, 190, 50, 'Back to Home', (70,20,20), (130,40,40))

    def render_gameplay():
        y = 160
        speed = settings_dict.get('gameplay', {}).get('ball_start_speed', 4.0)
        txt = fonts['small'].render(f'Ball Starting Speed:  {speed:.1f}', True, WHITE)
        screen.blit(txt, (80, y))
        slider_y = y + 36
        draw_slider(80, slider_y, 500, 20, speed, 2.0, 8.0)
        if _click[0]:
            mx, my = pygame.mouse.get_pos()
            if 80 <= mx <= 580 and abs(my - slider_y - 10) <= 20:
                new_speed = 2.0 + (mx - 80) / 500.0 * 6.0
                settings_dict['gameplay']['ball_start_speed'] = round(new_speed, 1)
        y += 80
        inc_pct = settings_dict.get('gameplay', {}).get('ball_speed_increase_pct', 5.0)
        txt = fonts['small'].render(f'Speed Increase per Hit:  {inc_pct:.1f}%', True, WHITE)
        screen.blit(txt, (80, y))
        slider_y = y + 36
        draw_slider(80, slider_y, 500, 20, inc_pct, 1.0, 15.0)
        if _click[0]:
            mx, my = pygame.mouse.get_pos()
            if 80 <= mx <= 580 and abs(my - slider_y - 10) <= 20:
                new_pct = 1.0 + (mx - 80) / 500.0 * 14.0
                settings_dict['gameplay']['ball_speed_increase_pct'] = round(new_pct, 1)
        y += 80
        txt = fonts['small'].render('Winning Score', True, WHITE)
        screen.blit(txt, (80, y))
        scores = [5, 10, 15, 20]
        bx = 80
        for s in scores:
            active = settings_dict.get('gameplay', {}).get('winning_score', 5) == s
            c = (40, 120, 40) if active else (60, 60, 60)
            hover_c = (40, 120, 40) if active else (90, 90, 90)
            btn = Button(bx, y + 36, 100, 40, str(s), c, hover_c)
            btn.draw(screen, fonts['small'])
            if _click[0] and btn.rect.collidepoint(_click_pos[0], _click_pos[1]):                
                settings_dict['gameplay']['winning_score'] = s
                _click[0] = False
                _click_pos[0] = -1
                _click_pos[1] = -1
                settings_mod.save_settings(settings_dict)
            bx += 120
        y += 96
        txt = fonts['small'].render('Difficulty', True, WHITE)
        screen.blit(txt, (80, y))
        diffs = ['Easy', 'Normal', 'Hard']
        diff_colors = {'Easy': (20, 100, 20), 'Normal': (100, 80, 10), 'Hard': (120, 20, 20)}
        bx = 80
        for d in diffs:
            active = settings_dict.get('gameplay', {}).get('difficulty', 'Normal') == d
            c = diff_colors[d] if active else (60, 60, 60)
            btn = Button(bx, y + 36, 140, 40, d, c, (80, 150, 80))
            btn.draw(screen, fonts['small'])
            if _click[0] and btn.rect.collidepoint(_click_pos[0], _click_pos[1]):
                settings_dict['gameplay']['difficulty'] = d
                _click[0] = False
                settings_mod.save_settings(settings_dict)
            bx += 160

    def render_audio():
        y = 160
        mv = settings_dict.get('audio', {}).get('master_volume', 0.8)
        txt = fonts['small'].render(f'Master Volume:  {int(mv * 100)}%', True, WHITE)
        screen.blit(txt, (80, y))
        slider_y = y + 36
        draw_slider(80, slider_y, 500, 20, mv, 0.0, 1.0)
        if _click[0]:
            mx, my = pygame.mouse.get_pos()
            if 80 <= mx <= 580 and abs(my - slider_y - 10) <= 20:
                settings_dict['audio']['master_volume'] = round((mx - 80) / 500.0, 2)
                pygame.mixer.music.set_volume(
                    settings_dict['audio']['bgm_volume'] *
                    settings_dict['audio']['master_volume'])
        y += 80
        bv = settings_dict.get('audio', {}).get('bgm_volume', 0.4)
        txt = fonts['small'].render(f'Background Music:  {int(bv * 100)}%', True, WHITE)
        screen.blit(txt, (80, y))
        slider_y = y + 36
        draw_slider(80, slider_y, 500, 20, bv, 0.0, 1.0)
        if _click[0]:
            mx, my = pygame.mouse.get_pos()
            if 80 <= mx <= 580 and abs(my - slider_y - 10) <= 20:
                settings_dict['audio']['bgm_volume'] = round((mx - 80) / 500.0, 2)
                pygame.mixer.music.set_volume(
                    settings_dict['audio']['bgm_volume'] *
                    settings_dict['audio']['master_volume'])
        y += 80
        sv = settings_dict.get('audio', {}).get('sfx_volume', 0.7)
        txt = fonts['small'].render(f'Sound Effects:  {int(sv * 100)}%', True, WHITE)
        screen.blit(txt, (80, y))
        slider_y = y + 36
        draw_slider(80, slider_y, 500, 20, sv, 0.0, 1.0)
        if _click[0]:
            mx, my = pygame.mouse.get_pos()
            if 80 <= mx <= 580 and abs(my - slider_y - 10) <= 20:
                settings_dict['audio']['sfx_volume'] = round((mx - 80) / 500.0, 2)
                sv_new = settings_dict['audio']['sfx_volume']
                mv_new = settings_dict['audio']['master_volume']
                for snd in _SOUND_CACHE.values():
                    if snd:
                        try:
                            snd.set_volume(sv_new * mv_new)
                        except Exception:
                            pass
                settings_mod.save_settings(settings_dict)
        y += 80
        mute = settings_dict.get('audio', {}).get('mute', False)
        c = (180, 30, 30) if mute else (60, 60, 60)
        hover_c = (220, 50, 50) if mute else (90, 90, 90)
        label = 'Mute: ON' if mute else 'Mute: OFF'
        btn = Button(80, y, 160, 40, label, c, hover_c)
        btn.draw(screen, fonts['small'])
        if _click[0] and btn.rect.collidepoint(_click_pos[0], _click_pos[1]):
            settings_dict['audio']['mute'] = not mute
            if settings_dict['audio']['mute']:
                pygame.mixer.music.pause()
                pygame.mixer.stop()
            else:
                pygame.mixer.music.unpause()
            _click[0] = False
            settings_mod.save_settings(settings_dict)

    def render_display():
        y = 160
        toggles = [
            ('show_fps',   'display', 'Show FPS Counter'),
            ('effects',    'display', 'Particle Effects'),
            ('court',      'display', 'Show Court Lines'),
        ]
        for key, section, label in toggles:
            val = settings_dict.get(section, {}).get(key, True)
            c = (40, 120, 40) if val else (60, 60, 60)
            hover_c = (40, 120, 40) if val else (90, 90, 90)
            status = 'ON' if val else 'OFF'
            btn = Button(80, y, 300, 40, f'{label}:  {status}', c, hover_c)
            btn.draw(screen, fonts['small'])
            if _click[0] and btn.rect.collidepoint(_click_pos[0], _click_pos[1]):
                settings_dict[section][key] = not val
                _click[0] = False
                settings_mod.save_settings(settings_dict)
            y += 66
        txt = fonts['tiny'].render('Resolution: 1280 x 720  (fixed)', True, LIGHT_GRAY)
        screen.blit(txt, (80, y))

    def render_controls():
        y = 160
        txt = fonts['small'].render('Current Key Bindings  (editing not yet supported)', True, CYAN)
        screen.blit(txt, (80, y))
        y += 50
        bindings = [
            ('Player 1 Move Up',   'controls', 'p1_up',   'W'),
            ('Player 1 Move Down', 'controls', 'p1_down', 'S'),
            ('Player 2 Move Up',   'controls', 'p2_up',   'UP'),
            ('Player 2 Move Down', 'controls', 'p2_down', 'DOWN'),
        ]
        for label, section, key, default in bindings:
            val = settings_dict.get(section, {}).get(key, default).upper()
            t = fonts['small'].render(label, True, LIGHT_GRAY)
            screen.blit(t, (100, y))
            key_box = pygame.Rect(460, y - 4, 120, 36)
            pygame.draw.rect(screen, (50, 50, 80), key_box, border_radius=6)
            pygame.draw.rect(screen, CYAN, key_box, 2, border_radius=6)
            kt = fonts['small'].render(val, True, WHITE)
            screen.blit(kt, (key_box.centerx - kt.get_width() // 2,
                             key_box.centery - kt.get_height() // 2))
            y += 56

    def render_accessibility():
        y = 160
        options = [
            ('colorblind',    'accessibility', 'Colorblind Mode',
             'Changes court color for red-green colorblindness'),
            ('high_contrast', 'accessibility', 'High Contrast Mode',
             'All game objects rendered in white'),
        ]
        for key, section, label, desc in options:
            val = settings_dict.get(section, {}).get(key, False)
            c = (40, 120, 40) if val else (60, 60, 60)
            hover_c = (40, 120, 40) if val else (90, 90, 90)
            status = 'ON' if val else 'OFF'
            btn = Button(80, y, 320, 40, f'{label}:  {status}', c, hover_c)
            btn.draw(screen, fonts['small'])
            if _click[0] and btn.rect.collidepoint(_click_pos[0], _click_pos[1]):
                settings_dict[section][key] = not val
                _click[0] = False
                settings_mod.save_settings(settings_dict)
            dt = fonts['tiny'].render(desc, True, LIGHT_GRAY)
            screen.blit(dt, (90, y + 46))
            y += 90

    def draw_slider(x, y, w, h, value, min_v, max_v):
        pygame.draw.rect(screen, LIGHT_GRAY, (x, y, w, h), border_radius=6)
        norm_val = (value - min_v) / (max_v - min_v) if max_v > min_v else 0.5
        inner_w = int((w - 8) * max(0, min(1, norm_val)))
        pygame.draw.rect(screen, CYAN, (x+4, y+4, inner_w, h-8), border_radius=6)

    while running:
        _click[0] = False
        _click_pos[0] = -1
        _click_pos[1] = -1
        # enforce mute state on every frame regardless of active tab
        if settings_dict.get('audio', {}).get('mute', False):
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()
        else:
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.unpause()
        # enforce mute state on every frame regardless of active tab
        if settings_dict.get('audio', {}).get('mute', False):
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()
        else:
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.unpause()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                _click[0] = True
                _click_pos[0] = event.pos[0]
                _click_pos[1] = event.pos[1]
                tab_rects = [pygame.Rect(j * (WIDTH // len(sections)), 67, WIDTH // len(sections), 52)
                             for j in range(len(sections))]
                for j, rect in enumerate(tab_rects):
                    if rect.collidepoint(event.pos):
                        current_section = j

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    settings_mod.save_settings(settings_dict)
                    return
                if event.key == pygame.K_LEFT:
                    current_section = (current_section - 1) % len(sections)
                if event.key == pygame.K_RIGHT:
                    current_section = (current_section + 1) % len(sections)

        screen.fill(DARK_GRAY)
        title = fonts['big'].render('SETTINGS', True, CYAN)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 30))
        pygame.draw.line(screen, LIGHT_GRAY, (40, 80), (WIDTH - 40, 80), 1)
        tab_y = 95
        tab_w = WIDTH // len(sections)
        for i, sec in enumerate(sections):
            mouse_pos = pygame.mouse.get_pos()
            tab_rect = pygame.Rect(i * tab_w, 67, tab_w, 52)
            if i == current_section:
                col = CYAN
            elif tab_rect.collidepoint(mouse_pos):
                col = WHITE
            else:
                col = LIGHT_GRAY
            t = fonts['small'].render(sec, True, col)
            x_pos = i * tab_w + (tab_w // 2) - t.get_width() // 2
            screen.blit(t, (x_pos, tab_y))
            if i == current_section:
                pygame.draw.line(screen, CYAN,
                    (x_pos, tab_y + 36),
                    (x_pos + t.get_width(), tab_y + 36), 3)
            if i > 0:
                pygame.draw.line(screen, LIGHT_GRAY,
                    (i * tab_w, tab_y),
                    (i * tab_w, tab_y + 40), 1)

        pygame.draw.line(screen, LIGHT_GRAY, (40, tab_y + 45), (WIDTH - 40, tab_y + 45), 1)
        if current_section == 0:
            render_gameplay()
        elif current_section == 1:
            render_audio()
        elif current_section == 2:
            render_display()
        elif current_section == 3:
            render_controls()
        elif current_section == 4:
            render_accessibility()

        back_btn.draw(screen, fonts['small'])
        if _click[0] and back_btn.rect.collidepoint(_click_pos[0], _click_pos[1]):
            settings_mod.save_settings(settings_dict)
            return

        pygame.display.flip()
        clock.tick(30)

# ─── Game update ─────────────────────────────────────────
def update_game(node, keys, mode, sounds, particles, trail, settings_dict, dt):
    if node.countdown_active:
        node.update_countdown(dt)
        return

    if node.game_status != 1:
        return

    ball_speed = max(abs(node.ball_vx), abs(node.ball_vy), 1.0)
    paddle_speed = ball_speed * 0.88
    paddle_speed = min(paddle_speed, ball_speed * 0.95)
    paddle_speed = max(3.0, min(paddle_speed, 20.0))

    # Player 1 always uses W/S
    if keys[pygame.K_w]:
        node.paddle1_y = max(node.paddle1_y - paddle_speed, PADDLE_H//2)
    if keys[pygame.K_s]:
        node.paddle1_y = min(node.paddle1_y + paddle_speed, HEIGHT - PADDLE_H//2)

    # Player 2: keyboard in local 2-player, AI in single player, ROS topic in network
    if mode == 2:
        if keys[pygame.K_UP]:
            node.paddle2_y = max(node.paddle2_y - paddle_speed, PADDLE_H//2)
        if keys[pygame.K_DOWN]:
            node.paddle2_y = min(node.paddle2_y + paddle_speed, HEIGHT - PADDLE_H//2)
    elif mode == 3:
        # Network mode: paddle2 driven by paddle_callback via /pong/paddle_input
        pass
    elif mode == 1:
        # AI
        target = node.ball_y + random.uniform(-15, 15)
        difficulty = settings_dict.get('gameplay', {}).get('difficulty', 'Normal')
        diff_mult = {'Easy': 0.6, 'Normal': 0.85, 'Hard': 0.98}.get(difficulty, 0.85)
        ai_speed = min(paddle_speed * diff_mult, 20.0)
        if node.paddle2_y < target - 5:
            node.paddle2_y = min(node.paddle2_y + ai_speed, HEIGHT - PADDLE_H//2)
        elif node.paddle2_y > target + 5:
            node.paddle2_y = max(node.paddle2_y - ai_speed, PADDLE_H//2)

    # Move ball
    node.ball_x += node.ball_vx
    node.ball_y += node.ball_vy

    trail.append((node.ball_x, node.ball_y))
    if len(trail) > 12:
        trail.pop(0)

    # Wall bounce
    if node.ball_y <= BALL_SIZE:
        node.ball_vy = abs(node.ball_vy)
        try: sounds['wall'].play()
        except Exception: pass
        if settings_dict.get('display', {}).get('effects', True):
            for _ in range(5):
                particles.append(Particle(node.ball_x, node.ball_y, CYAN))
    if node.ball_y >= HEIGHT - BALL_SIZE:
        node.ball_vy = -abs(node.ball_vy)
        try: sounds['wall'].play()
        except Exception: pass
        if settings_dict.get('display', {}).get('effects', True):
            for _ in range(5):
                particles.append(Particle(node.ball_x, node.ball_y, CYAN))

    # Paddle 1 collision
    if (node.ball_x - BALL_SIZE <= LEFT_MARGIN + PADDLE_W and
            node.ball_x > LEFT_MARGIN - 10 and
            abs(node.ball_y - node.paddle1_y) <= PADDLE_H//2):
        inc_pct = settings_dict.get('gameplay', {}).get('ball_speed_increase_pct', 5.0) / 100.0
        node.ball_vx = abs(node.ball_vx) * (1.0 + inc_pct)
        offset = (node.ball_y - node.paddle1_y) / (PADDLE_H/2)
        node.ball_vy = offset * max(6, BALL_SIZE//1)
        node.speed_mult = min(node.speed_mult + inc_pct, 5.0)
        try: sounds['paddle'].play()
        except Exception: pass
        if settings_dict.get('display', {}).get('effects', True):
            for _ in range(8):
                particles.append(Particle(node.ball_x, node.ball_y, GREEN))

    # Paddle 2 collision
    if (node.ball_x + BALL_SIZE >= WIDTH - LEFT_MARGIN - PADDLE_W and
            node.ball_x < WIDTH - LEFT_MARGIN + 10 and
            abs(node.ball_y - node.paddle2_y) <= PADDLE_H//2):
        inc_pct = settings_dict.get('gameplay', {}).get('ball_speed_increase_pct', 5.0) / 100.0
        node.ball_vx = -abs(node.ball_vx) * (1.0 + inc_pct)
        offset = (node.ball_y - node.paddle2_y) / (PADDLE_H/2)
        node.ball_vy = offset * max(6, BALL_SIZE//1)
        node.speed_mult = min(node.speed_mult + inc_pct, 5.0)
        try: sounds['paddle'].play()
        except Exception: pass
        if settings_dict.get('display', {}).get('effects', True):
            for _ in range(8):
                particles.append(Particle(node.ball_x, node.ball_y, RED))

    # Cap speed
    node.ball_vx = max(-20.0, min(20.0, node.ball_vx))
    node.ball_vy = max(-15.0, min(15.0, node.ball_vy))

    # Scoring - Left side (Player 2 scores)
    if node.ball_x <= 0:
        node.score2 += 1
        try: sounds['score'].play()
        except Exception: pass
        if settings_dict.get('display', {}).get('effects', True):
            for _ in range(15):
                particles.append(Particle(LEFT_MARGIN, node.ball_y, RED))
        target_win = settings_dict.get('gameplay', {}).get('winning_score', WIN_SCORE)
        if node.score2 >= target_win:
            node.game_status = 3
            try: sounds['win'].play()
            except Exception: pass
            w = 'ai' if mode == 1 else 'player2'
            node.publish_score_event(2, 'win', w)
            if settings_dict.get('display', {}).get('effects', True):
                for _ in range(30):
                    particles.append(Particle(
                        random.randint(0, WIDTH),
                        random.randint(0, HEIGHT), RED))
        else:
            node.publish_score_event(2, 'score', '')
            node.start_countdown(2)
        trail.clear()

    # Scoring - Right side (Player 1 scores)
    elif node.ball_x >= WIDTH:
        node.score1 += 1
        try: sounds['score'].play()
        except Exception: pass
        if settings_dict.get('display', {}).get('effects', True):
            for _ in range(15):
                particles.append(Particle(WIDTH-LEFT_MARGIN, node.ball_y, GREEN))
        target_win = settings_dict.get('gameplay', {}).get('winning_score', WIN_SCORE)
        if node.score1 >= target_win:
            node.game_status = 2
            try: sounds['win'].play()
            except Exception: pass
            node.publish_score_event(1, 'win', 'player1')
            if settings_dict.get('display', {}).get('effects', True):
                for _ in range(30):
                    particles.append(Particle(
                        random.randint(0, WIDTH),
                        random.randint(0, HEIGHT), GREEN))
        else:
            node.publish_score_event(1, 'score', '')
            node.start_countdown(1)
        trail.clear()

# ─── Main ────────────────────────────────────────────────
def main(args=None):
    rclpy.init(args=args)

    settings = settings_mod.load_settings()
    node = PongNode(settings)

    ros_thread = threading.Thread(
        target=rclpy.spin, args=(node,), daemon=True)
    ros_thread.start()

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('ROS 2 Pong — Group 8')
    clock  = pygame.time.Clock()

    sounds = load_sounds(settings)
    start_home_bgm(settings)

    fonts = {
        'title':  pygame.font.Font(None, 95),
        'big':    pygame.font.Font(None, 70),
        'medium': pygame.font.Font(None, 48),
        'small':  pygame.font.Font(None, 34),
        'tiny':   pygame.font.Font(None, 26),
    }

    help_btn     = Button(WIDTH - 220, 20, 90, 44, 'Help', (30, 30, 40), (60, 60, 80))
    settings_btn = Button(WIDTH - 120, 20, 100, 44, 'Settings', (30, 30, 40), (60, 60, 80))

    home_buttons = [
        Button(WIDTH//2-220, 210, 440, 68, 'Single Player',  (20,70,20),  (40,130,40)),
        Button(WIDTH//2-220, 300, 440, 68, 'Two Players',     (80,50,10),  (150,90,20)),
        Button(WIDTH//2-220, 390, 440, 68, 'Across 2 PCs',   (20,40,110), (40,80,190)),
    ]
    back_btn = Button(WIDTH - 210, HEIGHT - 70, 190, 50, 'Back to Home', (70,20,20), (130,40,40))
    help_back_btn = Button(WIDTH - 210, HEIGHT - 70, 190, 50, 'Back to Home', (70,20,20), (130,40,40))
    state     = 'home'
    mode      = 1
    particles = []
    trail     = []
    current_bgm = 'home'
    help_tab = 0
    help_scroll = 0

    running = True
    prev_time = time.time()

    while running:
        dt = time.time() - prev_time
        prev_time = time.time()
        dt = max(0.001, min(dt, 0.05))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if state == 'help':
                if event.type == pygame.MOUSEWHEEL:
                    help_scroll = max(0, min(1000, help_scroll - event.y * 28))
                if event.type == pygame.MOUSEBUTTONDOWN:
                    tab1_rect = pygame.Rect(WIDTH//2 - 220, 12, 180, 32)
                    tab2_rect = pygame.Rect(WIDTH//2 + 20, 12, 190, 32)
                    if help_back_btn.rect.collidepoint(event.pos):
                        state = 'home'
                    elif tab1_rect.collidepoint(event.pos):
                        help_tab = 0
                        help_scroll = 0
                    elif tab2_rect.collidepoint(event.pos):
                        help_tab = 1
                        help_scroll = 0
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                        state = 'home'
                    elif event.key == pygame.K_UP:
                        help_scroll = max(0, help_scroll - 28)
                    elif event.key == pygame.K_DOWN:
                        help_scroll = min(1000, help_scroll + 28)

            elif state == 'home':
                for i, btn in enumerate(home_buttons):
                    if btn.is_clicked(event):
                        try: sounds['click'].play()
                        except Exception: pass
                        if i == 2:
                            state = 'network'
                        else:
                            mode = i + 1
                            node._network_mode = False
                            node.reset_game()
                            trail.clear()
                            particles.clear()
                            state = 'game'
                if help_btn.is_clicked(event):
                    try: sounds['click'].play()
                    except Exception: pass
                    state = 'help'
                if settings_btn.is_clicked(event):
                    try: sounds['click'].play()
                    except Exception: pass
                    state = 'settings'

            elif state == 'game':
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        state = 'home'
                        particles.clear()
                        trail.clear()
                    if event.key == pygame.K_r:
                        node.reset_game()
                        trail.clear()
                        particles.clear()

            elif state == 'network':
                result = draw_network(screen, fonts, back_btn)
                if result == 'start':
                    try: sounds['click'].play()
                    except: pass
                    mode = 3
                    node._network_mode = True
                    node.reset_game()
                    trail.clear()
                    particles.clear()
                    state = 'game'
                elif result == 'join':
                    try: sounds['click'].play()
                    except: pass
                    node.enable_guest_mode()
                    state = 'guest'
                elif result == 'back':
                    try: sounds['click'].play()
                    except: pass
                    state = 'home'

            elif state == 'guest':
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        state = 'home'

        # BGM switching
        if state == 'home' and current_bgm != 'home':
            stop_bgm()
            start_home_bgm(settings)
            current_bgm = 'home'
        elif state == 'game' and current_bgm != 'game':
            stop_bgm()
            start_bgm(settings)
            current_bgm = 'game'

        if state == 'home':
            draw_home(screen, home_buttons, fonts, particles, help_btn, settings_btn)

        elif state == 'help':
            screen.fill(DARK_GRAY)

            tab1_rect = pygame.Rect(WIDTH//2 - 220, 12, 180, 32)
            tab2_rect = pygame.Rect(WIDTH//2 + 20, 12, 190, 32)
            tab1_text = fonts['small'].render('How to Play', True, CYAN if help_tab == 0 else LIGHT_GRAY)
            tab2_text = fonts['small'].render('Network Setup', True, CYAN if help_tab == 1 else LIGHT_GRAY)
            screen.blit(tab1_text, (tab1_rect.x + 10, tab1_rect.y + 4))
            screen.blit(tab2_text, (tab2_rect.x + 10, tab2_rect.y + 4))
            if help_tab == 0:
                pygame.draw.line(screen, CYAN, (tab1_rect.x, tab1_rect.bottom), (tab1_rect.right, tab1_rect.bottom), 2)
            else:
                pygame.draw.line(screen, CYAN, (tab2_rect.x, tab2_rect.bottom), (tab2_rect.right, tab2_rect.bottom), 2)

            if help_tab == 0:
                pygame.draw.line(screen, CYAN,
                    (WIDTH//2 - 200, 78), (WIDTH//2 + 200, 78), 1)

                # ── SECTION 1: CONTROLS ──
                sec1 = fonts['small'].render('CONTROLS', True, YELLOW)
                screen.blit(sec1, (80, 95))
                pygame.draw.line(screen, YELLOW, (80, 125), (WIDTH - 80, 125), 1)

                # Left sub-column - Player 1
                p1_title = fonts['small'].render('Player 1  (LEFT paddle)', True, GREEN)
                screen.blit(p1_title, (80, 138))
                p1_lines = ['W  →  Move Up', 'S  →  Move Down']
                y = 173
                for ln in p1_lines:
                    t = fonts['tiny'].render(ln, True, WHITE)
                    screen.blit(t, (80, y))
                    y += 28

                # Vertical divider
                pygame.draw.line(screen, LIGHT_GRAY,
                    (WIDTH//2, 138), (WIDTH//2, 245), 1)

                # Right sub-column - Player 2 / AI
                p2_title = fonts['small'].render('Player 2 / AI  (RIGHT paddle)', True, RED)
                screen.blit(p2_title, (WIDTH//2 + 20, 138))
                p2_lines = [
                    '\u2191  \u2192  Move Up',
                    '\u2193  \u2192  Move Down',
                ]
                y = 173
                for ln in p2_lines:
                    t = fonts['tiny'].render(ln, True, WHITE)
                    screen.blit(t, (WIDTH//2 + 20, y))
                    y += 28
                ai_note = fonts['tiny'].render(
                    'Single Player: right paddle = AI', True, LIGHT_GRAY)
                screen.blit(ai_note, (WIDTH//2 + 20, y + 8))

                # ── SECTION 2: GAME RULES ──
                pygame.draw.line(screen, LIGHT_GRAY, (80, 265), (WIDTH - 80, 265), 1)
                sec2 = fonts['small'].render('GAME RULES', True, YELLOW)
                screen.blit(sec2, (80, 278))
                pygame.draw.line(screen, YELLOW, (80, 308), (WIDTH - 80, 308), 1)

                win_score = settings.get('gameplay', {}).get('winning_score', 5)
                rules = [
                    f'First player to reach  {win_score}  points wins  (changeable in Settings)',
                    'Ball speed increases by a % after each paddle hit',
                    'After each point a 3-second countdown restarts the ball',
                    'Hit ball near paddle edge for sharper angle shots',
                ]
                y = 320
                for rule in rules:
                    bullet = fonts['tiny'].render(f'\u2022  {rule}', True, WHITE)
                    screen.blit(bullet, (80, y))
                    y += 32

                # ── SECTION 3: SHORTCUTS ──
                pygame.draw.line(screen, LIGHT_GRAY, (80, 460), (WIDTH - 80, 460), 1)
                sec3 = fonts['small'].render('KEYBOARD SHORTCUTS', True, YELLOW)
                screen.blit(sec3, (80, 472))
                pygame.draw.line(screen, YELLOW, (80, 502), (WIDTH - 80, 502), 1)

                shortcuts = [
                    ('ESC', 'Return to Home screen'),
                    ('R',   'Restart current game'),
                ]
                y = 515
                for key, desc in shortcuts:
                    key_box = pygame.Rect(80, y - 2, 44, 26)
                    pygame.draw.rect(screen, (50, 50, 80), key_box, border_radius=4)
                    pygame.draw.rect(screen, CYAN, key_box, 1, border_radius=4)
                    kt = fonts['tiny'].render(key, True, WHITE)
                    screen.blit(kt, (80 + 22 - kt.get_width()//2,
                                     y + 13 - kt.get_height()//2))
                    dt = fonts['tiny'].render(desc, True, LIGHT_GRAY)
                    screen.blit(dt, (134, y))
                    y += 32
            else:
                pygame.draw.line(screen, CYAN,
                    (WIDTH//2 - 220, 78), (WIDTH//2 + 220, 78), 1)

                header_y = 110 - help_scroll
                header = fonts['small'].render('STEP 1 — FIND YOUR IP', True, YELLOW)
                screen.blit(header, (80, header_y))
                pygame.draw.line(screen, YELLOW, (80, header_y + 28), (320, header_y + 28), 2)
                body_y = header_y + 42
                for line in [
                    'Both PCs: Open PowerShell → type ipconfig',
                    'Look for: Wireless LAN adapter Wi-Fi → IPv4 Address',
                    'Example: 192.168.43.145',
                    'OR: Check the Network screen in this game (shows automatically)',
                ]:
                    t = fonts['tiny'].render(line, True, WHITE)
                    screen.blit(t, (100, body_y))
                    body_y += 24

                header_y = body_y + 20
                header = fonts['small'].render('STEP 2 — CONNECT SAME NETWORK', True, YELLOW)
                screen.blit(header, (80, header_y))
                pygame.draw.line(screen, YELLOW, (80, header_y + 28), (360, header_y + 28), 2)
                body_y = header_y + 42
                for line in [
                    'Both PCs connect to SAME WiFi or phone hotspot',
                    'Both IPs must start with same numbers: 192.168.43.x',
                    'Test: ping <partner_ip> in PowerShell',
                ]:
                    t = fonts['tiny'].render(line, True, WHITE)
                    screen.blit(t, (100, body_y))
                    body_y += 24

                header_y = body_y + 20
                header = fonts['small'].render('STEP 3 — HOST PC (runs the game)', True, YELLOW)
                screen.blit(header, (80, header_y))
                pygame.draw.line(screen, YELLOW, (80, header_y + 28), (420, header_y + 28), 2)
                body_y = header_y + 42
                for line in [
                    'Open WSL2 terminal:',
                ]:
                    t = fonts['tiny'].render(line, True, WHITE)
                    screen.blit(t, (100, body_y))
                    body_y += 24
                for cmd in [
                    'source /opt/ros/jazzy/setup.bash',
                    'source ~/ros2_ws/install/setup.bash',
                    'ros2 run pong_game pygame_pong',
                ]:
                    cmd_box = pygame.Rect(120, body_y, 470, 30)
                    pygame.draw.rect(screen, (30, 70, 110), cmd_box, border_radius=4)
                    pygame.draw.rect(screen, CYAN, cmd_box, 1, border_radius=4)
                    t = fonts['tiny'].render(cmd, True, WHITE)
                    screen.blit(t, (132, body_y + 6))
                    body_y += 36
                for line in [
                    'Go to Network screen → Click START AS HOST',
                    'Your paddle: LEFT side | Controls: W = Up, S = Down',
                ]:
                    t = fonts['tiny'].render(line, True, WHITE)
                    screen.blit(t, (100, body_y))
                    body_y += 24

                header_y = body_y + 20
                header = fonts['small'].render('STEP 4 — PARTNER PC (keyboard only)', True, YELLOW)
                screen.blit(header, (80, header_y))
                pygame.draw.line(screen, YELLOW, (80, header_y + 28), (440, header_y + 28), 2)
                body_y = header_y + 42
                t = fonts['tiny'].render('Option A - Has ROS 2 + WSL2:', True, WHITE)
                screen.blit(t, (100, body_y))
                body_y += 24
                for cmd in [
                    'source /opt/ros/jazzy/setup.bash',
                    'source ~/ros2_ws/install/setup.bash',
                    'python3 ~/pong_controller.py <HOST_IP>',
                ]:
                    cmd_box = pygame.Rect(120, body_y, 470, 30)
                    pygame.draw.rect(screen, (30, 70, 110), cmd_box, border_radius=4)
                    pygame.draw.rect(screen, CYAN, cmd_box, 1, border_radius=4)
                    t = fonts['tiny'].render(cmd, True, WHITE)
                    screen.blit(t, (132, body_y + 6))
                    body_y += 36
                t = fonts['tiny'].render('Option B - Python on Windows only:', True, WHITE)
                screen.blit(t, (100, body_y))
                body_y += 24
                cmd_box = pygame.Rect(120, body_y, 470, 30)
                pygame.draw.rect(screen, (30, 70, 110), cmd_box, border_radius=4)
                pygame.draw.rect(screen, CYAN, cmd_box, 1, border_radius=4)
                t = fonts['tiny'].render(r'python C:\pong_controller.py <HOST_IP>', True, WHITE)
                screen.blit(t, (132, body_y + 6))
                body_y += 42
                for line in [
                    'Your paddle: RIGHT side | Controls: W = Up, S = Down',
                ]:
                    t = fonts['tiny'].render(line, True, WHITE)
                    screen.blit(t, (100, body_y))
                    body_y += 24

                header_y = body_y + 20
                header = fonts['small'].render('STEP 5 — VERIFY CONNECTION', True, YELLOW)
                screen.blit(header, (80, header_y))
                pygame.draw.line(screen, YELLOW, (80, header_y + 28), (360, header_y + 28), 2)
                body_y = header_y + 42
                for line in [
                    'Host terminal shows: "Received from <partner_ip>: paddle2_y=360"',
                    'Right paddle moves when partner presses W/S keys',
                ]:
                    t = fonts['tiny'].render(line, True, WHITE)
                    screen.blit(t, (100, body_y))
                    body_y += 24

                header_y = body_y + 20
                header = fonts['small'].render('STEP 6 — PLAY', True, YELLOW)
                screen.blit(header, (80, header_y))
                pygame.draw.line(screen, YELLOW, (80, header_y + 28), (240, header_y + 28), 2)
                body_y = header_y + 42
                for line in [
                    'Host PC: W/S = Left paddle (Player 1)',
                    'Partner: W/S or arrow keys = Right paddle (Player 2)',
                    'First to reach winning score wins!',
                ]:
                    t = fonts['tiny'].render(line, True, WHITE)
                    screen.blit(t, (100, body_y))
                    body_y += 24
                note = fonts['tiny'].render('Tip: keep both PCs on the same subnet and test ping before starting.', True, LIGHT_GRAY)
                screen.blit(note, (80, body_y + 12))
            
            # Draw back button last so it's on top
            help_back_btn.draw(screen, fonts['small'])
            pygame.display.flip()            

        elif state == 'settings':
            draw_settings(screen, fonts, settings, clock)
            settings_mod.save_settings(settings)
            state = 'home'

        elif state == 'guest':
            keys = pygame.key.get_pressed()
            paddle_speed = 3.0 * dt
            if keys[pygame.K_w]:
                node.guest_my_paddle_y = min(node.guest_my_paddle_y + paddle_speed, 2.25)
            if keys[pygame.K_s]:
                node.guest_my_paddle_y = max(node.guest_my_paddle_y - paddle_speed, -2.25)
            draw_guest(screen, node, fonts)

        elif state == 'game':
            keys = pygame.key.get_pressed()
            update_game(node, keys, mode, sounds, particles, trail, settings, dt)
            draw_game(screen, node, fonts, mode, particles, trail, settings, clock)

        clock.tick(FPS)

    stop_bgm()
    pygame.quit()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()