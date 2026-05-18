import rclpy
from rclpy.node import Node
from pong_msgs.msg import PongGameState, PongScore
import pygame
import sys
import threading
import random
import numpy as np
from pong_game.sound_gen import load_sounds, start_bgm, stop_bgm
from pong_game.sound_gen import load_sounds, start_bgm, stop_bgm

# Screen
WIDTH, HEIGHT = 900, 600
FPS = 60

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
PADDLE_W  = 14
PADDLE_H  = 90
BALL_SIZE = 11
WIN_SCORE = 5
AI_SPEED  = 4
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
    def __init__(self):
        super().__init__('pygame_pong')
        self.state_pub = self.create_publisher(
            PongGameState, '/pong/game_state', 10)
        self.score_pub = self.create_publisher(
            PongScore, '/pong/score_event', 10)
        self.create_timer(0.05, self.publish_state)
        self.get_logger().info('ROS2 Pong Node started!')

        # Game state
        self.ball_x    = float(WIDTH // 2)
        self.ball_y    = float(HEIGHT // 2)
        self.ball_vx   = random.choice([-4.0, 4.0])
        self.ball_vy   = random.choice([-3.0, 3.0])
        self.paddle1_y = float(HEIGHT // 2)
        self.paddle2_y = float(HEIGHT // 2)
        self.score1    = 0
        self.score2    = 0
        self.game_status = 1
        self.speed_mult  = 1.0

    def reset_game(self):
        self.ball_x      = float(WIDTH // 2)
        self.ball_y      = float(HEIGHT // 2)
        self.ball_vx     = random.choice([-4.0, 4.0])
        self.ball_vy     = random.choice([-3.0, 3.0])
        self.paddle1_y   = float(HEIGHT // 2)
        self.paddle2_y   = float(HEIGHT // 2)
        self.score1      = 0
        self.score2      = 0
        self.game_status = 1
        self.speed_mult  = 1.0
        self.publish_score_event(0, 'start', '')

    def reset_ball(self):
        self.ball_x  = float(WIDTH // 2)
        self.ball_y  = float(HEIGHT // 2)
        self.ball_vx = random.choice([-5.0, 5.0]) * self.speed_mult
        self.ball_vy = random.choice([-3.0, 3.0]) * self.speed_mult

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
def draw_bg(screen):
    screen.fill(DARK_GRAY)
    for y in range(0, HEIGHT, 25):
        pygame.draw.rect(screen, GRAY, (WIDTH//2-2, y, 4, 14))
    pygame.draw.rect(screen, BLUE, (0, 0, WIDTH, HEIGHT), 3)

def draw_home(screen, buttons, fonts, particles):
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

    title = fonts['title'].render('🏓 ROS 2 PONG', True, CYAN)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))

    sub = fonts['medium'].render('Group 8 | ITC Year 2 | Semester 2', True, LIGHT_GRAY)
    screen.blit(sub, (WIDTH//2 - sub.get_width()//2, 145))

    for btn in buttons:
        btn.draw(screen, fonts['small'])

    footer = fonts['tiny'].render(
        'ROS 2 Jazzy | Custom Messages | pong_msgs/PongGameState',
        True, LIGHT_GRAY)
    screen.blit(footer, (WIDTH//2 - footer.get_width()//2, HEIGHT-30))
    pygame.draw.rect(screen, BLUE, (0, 0, WIDTH, HEIGHT), 3)
    pygame.display.flip()

def draw_game(screen, node, fonts, mode, particles, trail):
    draw_bg(screen)

    # Trail
    for i, (tx, ty) in enumerate(trail):
        alpha = int((i / len(trail)) * 120)
        s = pygame.Surface((BALL_SIZE*2, BALL_SIZE*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (0, 220, 220, alpha), (BALL_SIZE, BALL_SIZE), BALL_SIZE)
        screen.blit(s, (int(tx)-BALL_SIZE, int(ty)-BALL_SIZE))

    # Particles
    for p in particles:
        p.update()
        p.draw(screen)
    particles[:] = [p for p in particles if p.life > 0]

    # Paddles with glow
    pygame.draw.rect(screen, (0, 100, 50),
        (48, int(node.paddle1_y)-PADDLE_H//2-2, PADDLE_W+4, PADDLE_H+4),
        border_radius=8)
    pygame.draw.rect(screen, GREEN,
        (50, int(node.paddle1_y)-PADDLE_H//2, PADDLE_W, PADDLE_H),
        border_radius=6)

    pygame.draw.rect(screen, (100, 20, 20),
        (WIDTH-50-PADDLE_W-2, int(node.paddle2_y)-PADDLE_H//2-2,
         PADDLE_W+4, PADDLE_H+4), border_radius=8)
    pygame.draw.rect(screen, RED,
        (WIDTH-50-PADDLE_W, int(node.paddle2_y)-PADDLE_H//2,
         PADDLE_W, PADDLE_H), border_radius=6)

    # Ball
    pygame.draw.circle(screen, CYAN,
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

    # Labels
    if mode == 1:
        l1 = fonts['tiny'].render('YOU (W/S)', True, GREEN)
        l2 = fonts['tiny'].render('AI', True, RED)
    elif mode == 2:
        l1 = fonts['tiny'].render('P1 W/S', True, GREEN)
        l2 = fonts['tiny'].render('P2 ↑↓', True, RED)
    else:
        l1 = fonts['tiny'].render('P1 W/S', True, GREEN)
        l2 = fonts['tiny'].render('P2 Network', True, RED)

    screen.blit(l1, (30, HEIGHT-30))
    screen.blit(l2, (WIDTH-120, HEIGHT-30))

    esc = fonts['tiny'].render('ESC=Home  R=Restart', True, LIGHT_GRAY)
    screen.blit(esc, (WIDTH//2 - esc.get_width()//2, HEIGHT-30))

    # Win screen
    if node.game_status in (2, 3):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        if node.game_status == 2:
            winner_txt = 'YOU WIN! 🎉' if mode == 1 else 'PLAYER 1 WINS! 🎉'
            color = GREEN
        else:
            winner_txt = 'AI WINS! 🤖' if mode == 1 else 'PLAYER 2 WINS! 🎉'
            color = RED

        wtxt = fonts['big'].render(winner_txt, True, color)
        screen.blit(wtxt, (WIDTH//2 - wtxt.get_width()//2, HEIGHT//2 - 60))

        hint = fonts['small'].render('R = Restart   ESC = Home', True, WHITE)
        screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT//2 + 20))

    pygame.display.flip()

def draw_network(screen, fonts, back_btn):
    screen.fill(DARK_GRAY)
    pygame.draw.rect(screen, BLUE, (0, 0, WIDTH, HEIGHT), 3)

    title = fonts['medium'].render('🌐 Network Multiplayer', True, CYAN)
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

# ─── Game update ─────────────────────────────────────────
def update_game(node, keys, mode, sounds, particles, trail):
    if node.game_status != 1:
        return

    speed = 6

    # Player 1
    if keys[pygame.K_w]:
        node.paddle1_y = max(node.paddle1_y - speed, PADDLE_H//2)
    if keys[pygame.K_s]:
        node.paddle1_y = min(node.paddle1_y + speed, HEIGHT - PADDLE_H//2)

    # Player 2 or AI
    if mode == 2 or mode == 3:
        if keys[pygame.K_UP]:
            node.paddle2_y = max(node.paddle2_y - speed, PADDLE_H//2)
        if keys[pygame.K_DOWN]:
            node.paddle2_y = min(node.paddle2_y + speed, HEIGHT - PADDLE_H//2)
    elif mode == 1:
        # AI with slight imperfection
        target = node.ball_y + random.uniform(-15, 15)
        if node.paddle2_y < target - 5:
            node.paddle2_y = min(node.paddle2_y + AI_SPEED * node.speed_mult,
                                 HEIGHT - PADDLE_H//2)
        elif node.paddle2_y > target + 5:
            node.paddle2_y = max(node.paddle2_y - AI_SPEED * node.speed_mult,
                                 PADDLE_H//2)

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
        sounds['wall'].play()
        for _ in range(5):
            particles.append(Particle(node.ball_x, node.ball_y, CYAN))
    if node.ball_y >= HEIGHT - BALL_SIZE:
        node.ball_vy = -abs(node.ball_vy)
        sounds['wall'].play()
        for _ in range(5):
            particles.append(Particle(node.ball_x, node.ball_y, CYAN))

    # Paddle 1 collision
    if (node.ball_x - BALL_SIZE <= 50 + PADDLE_W and
            node.ball_x > 40 and
            abs(node.ball_y - node.paddle1_y) <= PADDLE_H//2):
        node.ball_vx = abs(node.ball_vx) * 1.05
        offset = (node.ball_y - node.paddle1_y) / (PADDLE_H/2)
        node.ball_vy = offset * 6
        node.speed_mult = min(node.speed_mult + 0.05, 2.5)
        sounds['paddle'].play()
        for _ in range(8):
            particles.append(Particle(node.ball_x, node.ball_y, GREEN))

    # Paddle 2 collision
    if (node.ball_x + BALL_SIZE >= WIDTH - 50 - PADDLE_W and
            node.ball_x < WIDTH - 40 and
            abs(node.ball_y - node.paddle2_y) <= PADDLE_H//2):
        node.ball_vx = -abs(node.ball_vx) * 1.05
        offset = (node.ball_y - node.paddle2_y) / (PADDLE_H/2)
        node.ball_vy = offset * 6
        node.speed_mult = min(node.speed_mult + 0.05, 2.5)
        sounds['paddle'].play()
        for _ in range(8):
            particles.append(Particle(node.ball_x, node.ball_y, RED))

    # Cap speed
    node.ball_vx = max(-14.0, min(14.0, node.ball_vx))
    node.ball_vy = max(-12.0, min(12.0, node.ball_vy))

    # Scoring
    if node.ball_x <= 0:
        node.score2 += 1
        sounds['score'].play()
        for _ in range(15):
            particles.append(Particle(50, node.ball_y, RED))
        node.publish_score_event(2, 'score', '')
        node.reset_ball()
        trail.clear()

    elif node.ball_x >= WIDTH:
        node.score1 += 1
        sounds['score'].play()
        for _ in range(15):
            particles.append(Particle(WIDTH-50, node.ball_y, GREEN))
        node.publish_score_event(1, 'score', '')
        node.reset_ball()
        trail.clear()

    # Win
    if node.score1 >= WIN_SCORE:
        node.game_status = 2
        sounds['win'].play()
        w = 'player1' if mode != 1 else 'player1'
        node.publish_score_event(1, 'win', w)
        for _ in range(30):
            particles.append(Particle(
                random.randint(0, WIDTH),
                random.randint(0, HEIGHT), GREEN))

    elif node.score2 >= WIN_SCORE:
        node.game_status = 3
        sounds['win'].play()
        w = 'ai' if mode == 1 else 'player2'
        node.publish_score_event(2, 'win', w)
        for _ in range(30):
            particles.append(Particle(
                random.randint(0, WIDTH),
                random.randint(0, HEIGHT), RED))

# ─── Main ────────────────────────────────────────────────
def main(args=None):
    rclpy.init(args=args)
    node = PongNode()

    ros_thread = threading.Thread(
        target=rclpy.spin, args=(node,), daemon=True)
    ros_thread.start()

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('ROS 2 Pong — Group 8')
    clock  = pygame.time.Clock()

    sounds = load_sounds()
    bgm_file = start_bgm()

    fonts = {
        'title':  pygame.font.Font(None, 95),
        'big':    pygame.font.Font(None, 70),
        'medium': pygame.font.Font(None, 48),
        'small':  pygame.font.Font(None, 34),
        'tiny':   pygame.font.Font(None, 26),
    }

    home_buttons = [
        Button(WIDTH//2-220, 210, 440, 68,
               '🤖  1.  vs AI  (Single Player)',   (20,70,20),  (40,130,40)),
        Button(WIDTH//2-220, 300, 440, 68,
               '👥  2.  2 Players  (Same PC)',      (80,50,10),  (150,90,20)),
        Button(WIDTH//2-220, 390, 440, 68,
               '🌐  3.  Network  (2 PCs)',           (20,40,110), (40,80,190)),
    ]
    back_btn = Button(30, HEIGHT-65, 160, 45, '← Home', (70,20,20), (130,40,40))

    state     = 'home'
    mode      = 1
    particles = []
    trail     = []

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if state == 'home':
                for i, btn in enumerate(home_buttons):
                    if btn.is_clicked(event):
                        sounds['click'].play()
                        if i == 2:
                            state = 'network'
                        else:
                            mode = i + 1
                            node.reset_game()
                            trail.clear()
                            particles.clear()
                            state = 'game'

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
                    sounds['click'].play()
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

        if state == 'home':
            draw_home(screen, home_buttons, fonts, particles)

        elif state == 'game':
            keys = pygame.key.get_pressed()
            update_game(node, keys, mode, sounds, particles, trail)
            draw_game(screen, node, fonts, mode, particles, trail)

        elif state == 'network':
            draw_network(screen, fonts, back_btn)

        clock.tick(FPS)

    stop_bgm()
    pygame.quit()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
