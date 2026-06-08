import rclpy
from rclpy.node import Node
from pong_msgs.msg import PongGameState, PongScore
import pygame
import sys
import threading
import random
import numpy as np
import time
from pong_game.sound_gen import load_sounds, start_bgm, start_home_bgm, stop_bgm
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
        self.state_pub = self.create_publisher(
            PongGameState, '/pong/game_state', 10)
        self.score_pub = self.create_publisher(
            PongScore, '/pong/score_event', 10)
        self.create_timer(0.05, self.publish_state)
        self.get_logger().info('ROS2 Pong Node started!')

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
        """Start countdown timer after a score or at game start. scorer = 0 (start), 1 or 2 (who scored)"""
        self.countdown_active = True
        self.countdown_time = 0.0
        self.last_scorer = scorer
        self.ball_x = float(WIDTH // 2)
        self.ball_y = float(HEIGHT // 2)
        self.ball_vx = 0.0
        self.ball_vy = 0.0
        if scorer != 0:
            self.speed_mult = 1.0  # Reset speed multiplier only on score, not on game start

    def update_countdown(self, dt):
        """Update countdown and launch ball when ready. Returns True if countdown finished."""
        if not self.countdown_active:
            return False
        
        self.countdown_time += dt
        if self.countdown_time >= self.countdown_max:
            # Launch ball based on who served
            base_speed = float(self.settings.get('gameplay', {}).get('ball_start_speed', 4.0))
            if self.last_scorer == 0:
                # Game start: random direction
                self.ball_vx = base_speed * random.choice([-1, 1])
            elif self.last_scorer == 1:
                # Player 1 scored, ball goes toward player 2
                self.ball_vx = base_speed
            else:
                # Player 2 scored, ball goes toward player 1
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

# ─── Drawing helpers ─────────────────────────────────────
def draw_bg(screen, settings_dict):
    """Draw court background"""
    if settings_dict.get('display', {}).get('court', True):
        court_color = (10, 80, 40) if not settings_dict.get('accessibility', {}).get('colorblind', False) else (10, 40, 80)
        screen.fill(court_color)
        # shadow
        shadow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 60), (10, 10, WIDTH-20, HEIGHT-20), border_radius=12)
        screen.blit(shadow, (0, 0))

        # boundaries
        boundary_thick = int(6 * _SCALE)
        pygame.draw.rect(screen, WHITE, (20, 20, WIDTH-40, HEIGHT-40), boundary_thick, border_radius=6)

        # center dashed line
        dash_h = int(20 * _SCALE)
        gap = int(18 * _SCALE)
        x = WIDTH//2
        y = 30
        while y < HEIGHT-30:
            pygame.draw.rect(screen, WHITE, (x-2, y, 4, dash_h))
            y += dash_h + gap

        # service boxes
        box_w = int((WIDTH-200)//2)
        box_h = int((HEIGHT-120))
        pygame.draw.rect(screen, WHITE, (80, 60, box_w, box_h), 2)
        pygame.draw.rect(screen, WHITE, (WIDTH-80-box_w, 60, box_w, box_h), 2)

        # bleachers
        bleacher_color = (40, 40, 60)
        pygame.draw.rect(screen, bleacher_color, (0, 0, WIDTH, 24))
        pygame.draw.rect(screen, bleacher_color, (0, HEIGHT-24, WIDTH, 24))
    else:
        screen.fill(DARK_GRAY)

def draw_home(screen, buttons, fonts, particles, help_btn, settings_btn):
    """Draw home screen"""
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

    # utility buttons
    help_btn.draw(screen, fonts['tiny'])
    settings_btn.draw(screen, fonts['tiny'])

    footer = fonts['tiny'].render(
        'ROS 2 Jazzy | Custom Messages | pong_msgs/PongGameState',
        True, LIGHT_GRAY)
    screen.blit(footer, (WIDTH//2 - footer.get_width()//2, HEIGHT-30))
    pygame.draw.rect(screen, BLUE, (0, 0, WIDTH, HEIGHT), 3)
    pygame.display.flip()

def draw_countdown(screen, node, fonts):
    """Draw countdown number"""
    remaining = node.countdown_max - node.countdown_time
    countdown_num = max(0, int(remaining) + 1)
    if countdown_num > 0:
        if countdown_num == 3:
            color = RED
        elif countdown_num == 2:
            color = YELLOW
        else:
            color = GREEN
        
        # Draw large glowing number
        txt = fonts['big'].render(str(countdown_num), True, color)
        # Glow effect
        glow = pygame.Surface((txt.get_width() + 40, txt.get_height() + 40), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*color, 80), (txt.get_width()//2 + 20, txt.get_height()//2 + 20), txt.get_height()//2 + 15)
        screen.blit(glow, (WIDTH//2 - glow.get_width()//2, HEIGHT//2 - glow.get_height()//2))
        screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - txt.get_height()//2))

def draw_game(screen, node, fonts, mode, particles, trail, settings_dict):
    """Draw game screen"""
    draw_bg(screen, settings_dict)

    # Trail
    if settings_dict.get('display', {}).get('effects', True):
        for i, (tx, ty) in enumerate(trail):
            alpha = int((i / len(trail)) * 120) if trail else 0
            s = pygame.Surface((BALL_SIZE*2, BALL_SIZE*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (0, 220, 220, alpha), (BALL_SIZE, BALL_SIZE), BALL_SIZE)
            screen.blit(s, (int(tx)-BALL_SIZE, int(ty)-BALL_SIZE))

    # Particles
    if settings_dict.get('display', {}).get('effects', True):
        for p in particles:
            p.update()
            p.draw(screen)
        particles[:] = [p for p in particles if p.life > 0]

    # Paddles with glow
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

    # Ball
    ball_col = WHITE if settings_dict.get('accessibility', {}).get('high_contrast', False) else CYAN
    pygame.draw.circle(screen, ball_col,
        (int(node.ball_x), int(node.ball_y)), BALL_SIZE)
    pygame.draw.circle(screen, WHITE,
        (int(node.ball_x), int(node.ball_y)), BALL_SIZE-4)

    # Score
    s1 = fonts['big'].render(str(node.score1), True, GREEN)
    s2 = fonts['big'].render(str(node.score2), True, RED)
    screen.blit(s1, (WIDTH//2 - 80, 15))
    screen.blit(s2, (WIDTH//2 + 45, 15))

    # Speed indicator
    spd = fonts['tiny'].render(
        f'Speed: {node.speed_mult:.1f}x', True, YELLOW)
    screen.blit(spd, (WIDTH//2 - spd.get_width()//2, 75))

    esc = fonts['tiny'].render('ESC=Home  R=Restart', True, LIGHT_GRAY)
    screen.blit(esc, (WIDTH//2 - esc.get_width()//2, HEIGHT-30))

    # Countdown overlay
    if node.countdown_active:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        screen.blit(overlay, (0, 0))
        draw_countdown(screen, node, fonts)

    # Win screen
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
    """Draw network mode screen"""
    screen.fill(DARK_GRAY)
    pygame.draw.rect(screen, BLUE, (0, 0, WIDTH, HEIGHT), 3)

    title = fonts['medium'].render('[NET] Network Multiplayer', True, CYAN)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 40))

    lines = [
        ('On PC 2, run these commands:', WHITE),
        ('', WHITE),
        ('1. source /opt/ros/jazzy/setup.bash', YELLOW),
        ('2. source ~/ros2_ws/install/setup.bash', YELLOW),
        ('3. ros2 run pong_game keyboard_controller', GREEN),
        ('', WHITE),
        ('Both PCs must be on the same WiFi/Hotspot', CYAN),
        ('Player 1 (this PC): W / S keys', GREEN),
        ('Player 2 (other PC): W / S keys', RED),
        ('', WHITE),
        ('Press SPACE to start game as host', WHITE),
    ]

    y = 120
    for line, color in lines:
        if line == '':
            y += 15
            continue
        txt = fonts['small'].render(line, True, color)
        screen.blit(txt, (WIDTH//2 - txt.get_width()//2, y))
        y += 38

    back_btn.draw(screen, fonts['small'])
    pygame.display.flip()

def draw_settings(screen, fonts, settings_dict, clock):
    """Draw professional settings panel with sections"""
    running = True
    current_section = 0
    sections = ['GAMEPLAY', 'AUDIO', 'DISPLAY', 'CONTROLS', 'ACCESSIBILITY']
    
    back_btn = Button(WIDTH - 210, HEIGHT - 70, 190, 50, '<- Back to Home', (70,20,20), (130,40,40))
    
    def render_gameplay():
        y = 100
        # Ball starting speed
        speed = settings_dict.get('gameplay', {}).get('ball_start_speed', 4.0)
        txt = fonts['small'].render('Ball Starting Speed', True, WHITE)
        screen.blit(txt, (80, y))
        slider_y = y+40
        draw_slider(80, slider_y, 500, 24, speed, 2.0, 8.0)
        if mouse_just_clicked:
            mx, my = pygame.mouse.get_pos()
            if 80 <= mx <= 580 and abs(my - slider_y - 12) <= 20:
                new_speed = 2.0 + (mx - 80) / 500.0 * 6.0
                settings_dict['gameplay']['ball_start_speed'] = round(new_speed, 1)
        
        y += 80
        # Speed increase rate
        inc_pct = settings_dict.get('gameplay', {}).get('ball_speed_increase_pct', 5.0)
        txt = fonts['small'].render('Speed Increase per Hit', True, WHITE)
        screen.blit(txt, (80, y))
        slider_y = y+40
        draw_slider(80, slider_y, 500, 24, inc_pct / 100.0, 0.01, 0.15)
        if mouse_just_clicked:
            mx, my = pygame.mouse.get_pos()
            if 80 <= mx <= 580 and abs(my - slider_y - 12) <= 20:
                new_pct = 1.0 + (mx - 80) / 500.0 * 14.0
                settings_dict['gameplay']['ball_speed_increase_pct'] = round(new_pct, 1)
        
        y += 80
        # Winning score
        txt = fonts['small'].render('Winning Score', True, WHITE)
        screen.blit(txt, (80, y))
        scores = [5, 10, 15, 20]
        bx = 80
        for s in scores:
            c = (40, 120, 40) if settings_dict.get('gameplay', {}).get('winning_score', 5) == s else (60, 60, 60)
            btn = Button(bx, y+40, 100, 44, str(s), c, (80, 150, 80))
            btn.draw(screen, fonts['small'])
            if mouse_just_clicked and btn.rect.collidepoint(pygame.mouse.get_pos()):
                settings_dict['gameplay']['winning_score'] = s
            bx += 120
        
        y += 100
        # Difficulty
        txt = fonts['small'].render('Difficulty', True, WHITE)
        screen.blit(txt, (80, y))
        diffs = ['Easy', 'Normal', 'Hard']
        bx = 80
        for d in diffs:
            c = (40, 120, 40) if settings_dict.get('gameplay', {}).get('difficulty', 'Normal') == d else (60, 60, 60)
            btn = Button(bx, y+40, 140, 44, d, c, (80, 150, 80))
            btn.draw(screen, fonts['small'])
            if mouse_just_clicked and btn.rect.collidepoint(pygame.mouse.get_pos()):
                settings_dict['gameplay']['difficulty'] = d
            bx += 160
    
    def render_audio():
        y = 100
        # Master volume
        mv = settings_dict.get('audio', {}).get('master_volume', 0.8)
        txt = fonts['small'].render(f'Master Volume: {int(mv*100)}%', True, WHITE)
        screen.blit(txt, (80, y))
        slider_y = y+40
        draw_slider(80, slider_y, 500, 24, mv, 0.0, 1.0)
        if mouse_just_clicked:
            mx, my = pygame.mouse.get_pos()
            if 80 <= mx <= 580 and abs(my - slider_y - 12) <= 20:
                settings_dict['audio']['master_volume'] = round((mx - 80) / 500.0, 2)
        
        y += 90
        # BGM volume
        bv = settings_dict.get('audio', {}).get('bgm_volume', 0.4)
        txt = fonts['small'].render(f'Background Music: {int(bv*100)}%', True, WHITE)
        screen.blit(txt, (80, y))
        slider_y = y+40
        draw_slider(80, slider_y, 500, 24, bv, 0.0, 1.0)
        if mouse_just_clicked:
            mx, my = pygame.mouse.get_pos()
            if 80 <= mx <= 580 and abs(my - slider_y - 12) <= 20:
                settings_dict['audio']['bgm_volume'] = round((mx - 80) / 500.0, 2)
        
        y += 90
        # SFX volume
        sv = settings_dict.get('audio', {}).get('sfx_volume', 0.7)
        txt = fonts['small'].render(f'Sound Effects: {int(sv*100)}%', True, WHITE)
        screen.blit(txt, (80, y))
        slider_y = y+40
        draw_slider(80, slider_y, 500, 24, sv, 0.0, 1.0)
        if mouse_just_clicked:
            mx, my = pygame.mouse.get_pos()
            if 80 <= mx <= 580 and abs(my - slider_y - 12) <= 20:
                settings_dict['audio']['sfx_volume'] = round((mx - 80) / 500.0, 2)
        
        y += 90
        # Mute toggle
        mute = settings_dict.get('audio', {}).get('mute', False)
        c = (40, 120, 40) if mute else (60, 60, 60)
        btn = Button(80, y, 200, 44, 'Mute: ' + ('ON' if mute else 'OFF'), c, (80, 150, 80))
        btn.draw(screen, fonts['small'])
        if mouse_just_clicked and btn.rect.collidepoint(pygame.mouse.get_pos()):
            settings_dict['audio']['mute'] = not mute
    
    def render_display():
        y = 100
        # Fullscreen toggle
        fs = settings_dict.get('display', {}).get('fullscreen', False)
        c = (40, 120, 40) if fs else (60, 60, 60)
        btn = Button(80, y, 220, 44, 'Fullscreen: ' + ('ON' if fs else 'OFF'), c, (80, 150, 80))
        btn.draw(screen, fonts['small'])
        if mouse_just_clicked and btn.rect.collidepoint(pygame.mouse.get_pos()):
            settings_dict['display']['fullscreen'] = not fs
        
        y += 70
        # Resolution (informational for now)
        txt = fonts['small'].render('Resolution: 1280x720', True, LIGHT_GRAY)
        screen.blit(txt, (80, y))
        
        y += 70
        # Show FPS
        fps = settings_dict.get('display', {}).get('show_fps', False)
        c = (40, 120, 40) if fps else (60, 60, 60)
        btn = Button(80, y, 200, 44, 'Show FPS: ' + ('ON' if fps else 'OFF'), c, (80, 150, 80))
        btn.draw(screen, fonts['small'])
        if mouse_just_clicked and btn.rect.collidepoint(pygame.mouse.get_pos()):
            settings_dict['display']['show_fps'] = not fps
        
        y += 70
        # Effects
        eff = settings_dict.get('display', {}).get('effects', True)
        c = (40, 120, 40) if eff else (60, 60, 60)
        btn = Button(80, y, 200, 44, 'Effects: ' + ('ON' if eff else 'OFF'), c, (80, 150, 80))
        btn.draw(screen, fonts['small'])
        if mouse_just_clicked and btn.rect.collidepoint(pygame.mouse.get_pos()):
            settings_dict['display']['effects'] = not eff
    
    def render_controls():
        y = 100
        txt = fonts['small'].render('Current Key Bindings', True, CYAN)
        screen.blit(txt, (80, y))
        y += 50
        
        controls_text = [
            f"P1 Up:    {settings_dict.get('controls', {}).get('p1_up', 'w').upper()}",
            f"P1 Down:  {settings_dict.get('controls', {}).get('p1_down', 's').upper()}",
            f"P2 Up:    {settings_dict.get('controls', {}).get('p2_up', 'up').upper()}",
            f"P2 Down:  {settings_dict.get('controls', {}).get('p2_down', 'down').upper()}",
        ]
        for line in controls_text:
            t = fonts['small'].render(line, True, LIGHT_GRAY)
            screen.blit(t, (100, y))
            y += 50
        
        y += 30
        # Reset button
        btn = Button(80, y, 200, 44, 'Reset to Defaults', (70, 50, 50), (120, 80, 80))
        btn.draw(screen, fonts['small'])
        if mouse_just_clicked and btn.rect.collidepoint(pygame.mouse.get_pos()):
            settings_dict['controls'] = settings_mod.DEFAULTS['controls'].copy()
    
    def render_accessibility():
        y = 100
        # Colorblind mode
        cb = settings_dict.get('accessibility', {}).get('colorblind', False)
        c = (40, 120, 40) if cb else (60, 60, 60)
        btn = Button(80, y, 220, 44, 'Colorblind: ' + ('ON' if cb else 'OFF'), c, (80, 150, 80))
        btn.draw(screen, fonts['small'])
        if mouse_just_clicked and btn.rect.collidepoint(pygame.mouse.get_pos()):
            settings_dict['accessibility']['colorblind'] = not cb
        
        y += 70
        # Large text
        lt = settings_dict.get('accessibility', {}).get('large_text', False)
        c = (40, 120, 40) if lt else (60, 60, 60)
        btn = Button(80, y, 200, 44, 'Large Text: ' + ('ON' if lt else 'OFF'), c, (80, 150, 80))
        btn.draw(screen, fonts['small'])
        if mouse_just_clicked and btn.rect.collidepoint(pygame.mouse.get_pos()):
            settings_dict['accessibility']['large_text'] = not lt
        
        y += 70
        # High contrast
        hc = settings_dict.get('accessibility', {}).get('high_contrast', False)
        c = (40, 120, 40) if hc else (60, 60, 60)
        btn = Button(80, y, 220, 44, 'High Contrast: ' + ('ON' if hc else 'OFF'), c, (80, 150, 80))
        btn.draw(screen, fonts['small'])
        if mouse_just_clicked and btn.rect.collidepoint(pygame.mouse.get_pos()):
            settings_dict['accessibility']['high_contrast'] = not hc
    
    def draw_slider(x, y, w, h, value, min_v, max_v):
        pygame.draw.rect(screen, LIGHT_GRAY, (x, y, w, h), border_radius=6)
        norm_val = (value - min_v) / (max_v - min_v) if max_v > min_v else 0.5
        inner_w = int((w - 8) * max(0, min(1, norm_val)))
        pygame.draw.rect(screen, CYAN, (x+4, y+4, inner_w, h-8), border_radius=6)
    
    while running:
        mouse_just_clicked = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_just_clicked = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    settings_mod.save_settings(settings_dict)
                    return
                if event.key == pygame.K_LEFT:
                    current_section = (current_section - 1) % len(sections)
                if event.key == pygame.K_RIGHT:
                    current_section = (current_section + 1) % len(sections)
        
        screen.fill(DARK_GRAY)
        
        # Header
        title = fonts['big'].render('SETTINGS', True, CYAN)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 20))
        
        # Section tabs
        tab_y = 70
        for i, sec in enumerate(sections):
            col = CYAN if i == current_section else LIGHT_GRAY
            t = fonts['small'].render(sec, True, col)
            x_pos = 80 + i * 220
            screen.blit(t, (x_pos, tab_y))
            if i == current_section:
                pygame.draw.line(screen, CYAN, (x_pos, tab_y + 40), (x_pos + t.get_width(), tab_y + 40), 3)
        
        # Render current section
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
        
        # Back button
        back_btn.draw(screen, fonts['small'])
        if mouse_just_clicked and back_btn.rect.collidepoint(pygame.mouse.get_pos()):
            settings_mod.save_settings(settings_dict)
            return
        
        pygame.display.flip()
        clock.tick(30)

# ─── Game update ─────────────────────────────────────────
def update_game(node, keys, mode, sounds, particles, trail, settings_dict, dt):
    """Update game logic"""
    # Update countdown
    if node.countdown_active:
        node.update_countdown(dt)
        return  # Don't update game during countdown
    
    if node.game_status != 1:
        return

    # Calculate paddle speed from ball speed
    ball_speed = max(abs(node.ball_vx), abs(node.ball_vy), 1.0)
    paddle_speed = ball_speed * 0.88
    paddle_speed = min(paddle_speed, ball_speed * 0.95)
    paddle_speed = max(3.0, min(paddle_speed, 20.0))

    # Player 1
    if keys[pygame.K_w]:
        node.paddle1_y = max(node.paddle1_y - paddle_speed, PADDLE_H//2)
    if keys[pygame.K_s]:
        node.paddle1_y = min(node.paddle1_y + paddle_speed, HEIGHT - PADDLE_H//2)

    # Player 2 or AI
    if mode == 2 or mode == 3:
        if keys[pygame.K_UP]:
            node.paddle2_y = max(node.paddle2_y - paddle_speed, PADDLE_H//2)
        if keys[pygame.K_DOWN]:
            node.paddle2_y = min(node.paddle2_y + paddle_speed, HEIGHT - PADDLE_H//2)
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

    # Trail
    trail.append((node.ball_x, node.ball_y))
    if len(trail) > 12:
        trail.pop(0)

    # Wall bounce
    if node.ball_y <= BALL_SIZE:
        node.ball_vy = abs(node.ball_vy)
        try:
            sounds['wall'].play()
        except Exception:
            pass
        if settings_dict.get('display', {}).get('effects', True):
            for _ in range(5):
                particles.append(Particle(node.ball_x, node.ball_y, CYAN))
    if node.ball_y >= HEIGHT - BALL_SIZE:
        node.ball_vy = -abs(node.ball_vy)
        try:
            sounds['wall'].play()
        except Exception:
            pass
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
        try:
            sounds['paddle'].play()
        except Exception:
            pass
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
        try:
            sounds['paddle'].play()
        except Exception:
            pass
        if settings_dict.get('display', {}).get('effects', True):
            for _ in range(8):
                particles.append(Particle(node.ball_x, node.ball_y, RED))

    # Cap speed
    node.ball_vx = max(-20.0, min(20.0, node.ball_vx))
    node.ball_vy = max(-15.0, min(15.0, node.ball_vy))

    # Scoring - Left side (Player 2 scores)
    if node.ball_x <= 0:
        node.score2 += 1
        try:
            sounds['score'].play()
        except Exception:
            pass
        if settings_dict.get('display', {}).get('effects', True):
            for _ in range(15):
                particles.append(Particle(LEFT_MARGIN, node.ball_y, RED))
        
        # Check win condition
        target_win = settings_dict.get('gameplay', {}).get('winning_score', WIN_SCORE)
        if node.score2 >= target_win:
            # Player 2 wins
            node.game_status = 3
            try:
                sounds['win'].play()
            except Exception:
                pass
            w = 'ai' if mode == 1 else 'player2'
            node.publish_score_event(2, 'win', w)
            if settings_dict.get('display', {}).get('effects', True):
                for _ in range(30):
                    particles.append(Particle(
                        random.randint(0, WIDTH),
                        random.randint(0, HEIGHT), RED))
        else:
            # No win yet, start countdown
            node.publish_score_event(2, 'score', '')
            node.start_countdown(2)
        
        trail.clear()

    # Scoring - Right side (Player 1 scores)
    elif node.ball_x >= WIDTH:
        node.score1 += 1
        try:
            sounds['score'].play()
        except Exception:
            pass
        if settings_dict.get('display', {}).get('effects', True):
            for _ in range(15):
                particles.append(Particle(WIDTH-LEFT_MARGIN, node.ball_y, GREEN))
        
        # Check win condition
        target_win = settings_dict.get('gameplay', {}).get('winning_score', WIN_SCORE)
        if node.score1 >= target_win:
            # Player 1 wins
            node.game_status = 2
            try:
                sounds['win'].play()
            except Exception:
                pass
            w = 'player1' if mode != 1 else 'player1'
            node.publish_score_event(1, 'win', w)
            if settings_dict.get('display', {}).get('effects', True):
                for _ in range(30):
                    particles.append(Particle(
                        random.randint(0, WIDTH),
                        random.randint(0, HEIGHT), GREEN))
        else:
            # No win yet, start countdown
            node.publish_score_event(1, 'score', '')
            node.start_countdown(1)
        
        trail.clear()

# ─── Main ────────────────────────────────────────────────
def main(args=None):
    rclpy.init(args=args)
    
    # Load settings before creating node
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

    help_btn = Button(WIDTH - 220, 20, 90, 44, '? Help', (30, 30, 40), (60, 60, 80))
    settings_btn = Button(WIDTH - 120, 20, 100, 44, 'Settings', (30, 30, 40), (60, 60, 80))

    home_buttons = [
        Button(WIDTH//2-220, 210, 440, 68,
               '[AI]  Single Player',   (20,70,20),  (40,130,40)),
        Button(WIDTH//2-220, 300, 440, 68,
               '[2P]  Two Players',      (80,50,10),  (150,90,20)),
        Button(WIDTH//2-220, 390, 440, 68,
               '[NET] Across 2 PCs',     (20,40,110), (40,80,190)),
    ]
    back_btn = Button(WIDTH//2 - 80, HEIGHT - 80, 160, 50, '<- Home', (70,20,20), (130,40,40))

    state     = 'home'
    mode      = 1
    particles = []
    trail     = []
    current_bgm = 'home'

    running = True
    prev_time = time.time()

    while running:
        dt = time.time() - prev_time
        prev_time = time.time()
        dt = max(0.001, min(dt, 0.05))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if state == 'home':
                for i, btn in enumerate(home_buttons):
                    if btn.is_clicked(event):
                        try:
                            sounds['click'].play()
                        except Exception:
                            pass
                        if i == 2:
                            state = 'network'
                        else:
                            mode = i + 1
                            node.reset_game()
                            trail.clear()
                            particles.clear()
                            state = 'game'
                if help_btn.is_clicked(event):
                    try:
                        sounds['click'].play()
                    except Exception:
                        pass
                    state = 'help'
                if settings_btn.is_clicked(event):
                    try:
                        sounds['click'].play()
                    except Exception:
                        pass
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
                if back_btn.is_clicked(event):
                    try:
                        sounds['click'].play()
                    except Exception:
                        pass
                    state = 'home'
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        state = 'home'
                    if event.key == pygame.K_SPACE:
                        mode = 3
                        node.reset_game()
                        trail.clear()
                        particles.clear()
                        state = 'game'

        # BGM switching based on state
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
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 240))
            screen.blit(overlay, (0, 0))
            
            # Draw bordered box behind help text
            box_rect = pygame.Rect(WIDTH//2 - 320, 100, 640, 420)
            pygame.draw.rect(screen, (30, 30, 50), box_rect, border_radius=16)
            pygame.draw.rect(screen, CYAN, box_rect, 2, border_radius=16)
            
            title = fonts['big'].render('HOW TO PLAY', True, CYAN)
            screen.blit(title, (WIDTH//2 - title.get_width()//2, 40))
            lines = [
                'Player 1: W / S',
                'Player 2: Up / Down',
                f'First to {settings.get("gameplay",{}).get("winning_score",5)} wins',
                'Ball speed increases on each paddle hit',
                'ESC or click anywhere to return'
            ]
            y = 140
            for ln in lines:
                color = CYAN if 'ESC' in ln else WHITE
                t = fonts['medium'].render(ln, True, color)
                screen.blit(t, (WIDTH//2 - t.get_width()//2, y))
                y += 56
            pygame.display.flip()
            waiting = True
            while waiting:
                for ev in pygame.event.get():
                    if ev.type == pygame.QUIT:
                        running = False
                        waiting = False
                    if ev.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                        waiting = False
                        state = 'home'
                clock.tick(30)

        elif state == 'settings':
            draw_settings(screen, fonts, settings, clock)
            settings_mod.save_settings(settings)
            state = 'home'

        elif state == 'game':
            keys = pygame.key.get_pressed()
            update_game(node, keys, mode, sounds, particles, trail, settings, dt)
            draw_game(screen, node, fonts, mode, particles, trail, settings)

        elif state == 'network':
            draw_network(screen, fonts, back_btn)

        clock.tick(FPS)

    stop_bgm()
    pygame.quit()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
