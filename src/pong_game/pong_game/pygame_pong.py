import rclpy
from rclpy.node import Node
from pong_msgs.msg import PongGameState
import pygame
import sys
import threading
import math

# Arena settings
WIDTH, HEIGHT = 800, 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 100, 255)
YELLOW = (255, 255, 0)

class PongGame(Node):
    def __init__(self):
        super().__init__('pygame_pong')

        # Publishers & Subscribers
        self.state_pub = self.create_publisher(PongGameState, '/pong/game_state', 10)
        self.subscription = self.create_subscription(
            PongGameState, '/pong/paddle_input', self.paddle_callback, 10)

        # Game state
        self.ball_x = WIDTH // 2
        self.ball_y = HEIGHT // 2
        self.ball_vx = 4.0
        self.ball_vy = 3.0
        self.paddle1_y = HEIGHT // 2
        self.paddle2_y = HEIGHT // 2
        self.score1 = 0
        self.score2 = 0
        self.game_status = 1

        # Paddle settings
        self.paddle_w = 15
        self.paddle_h = 80
        self.paddle_speed = 6
        self.ball_size = 12

        # Timer to publish state
        self.create_timer(0.05, self.publish_state)
        self.get_logger().info('Pygame Pong started!')

    def paddle_callback(self, msg):
        # Scale from ROS coordinates to pixels
        self.paddle1_y = int((msg.paddle1_y / 3.0 + 0.5) * HEIGHT)
        self.paddle2_y = int((msg.paddle2_y / 3.0 + 0.5) * HEIGHT)

    def publish_state(self):
        msg = PongGameState()
        msg.ball_x = float(self.ball_x)
        msg.ball_y = float(self.ball_y)
        msg.ball_vel_x = float(self.ball_vx)
        msg.ball_vel_y = float(self.ball_vy)
        msg.paddle1_y = float(self.paddle1_y)
        msg.paddle2_y = float(self.paddle2_y)
        msg.score_player1 = self.score1
        msg.score_player2 = self.score2
        msg.game_status = self.game_status
        self.state_pub.publish(msg)

    def reset_ball(self):
        self.ball_x = WIDTH // 2
        self.ball_y = HEIGHT // 2
        self.ball_vx *= -1

    def update(self, keys):
        if self.game_status != 1:
            return

        # Player 1: W/S
        if keys[pygame.K_w]:
            self.paddle1_y = max(self.paddle1_y - self.paddle_speed, self.paddle_h // 2)
        if keys[pygame.K_s]:
            self.paddle1_y = min(self.paddle1_y + self.paddle_speed, HEIGHT - self.paddle_h // 2)

        # Player 2: Arrow keys
        if keys[pygame.K_UP]:
            self.paddle2_y = max(self.paddle2_y - self.paddle_speed, self.paddle_h // 2)
        if keys[pygame.K_DOWN]:
            self.paddle2_y = min(self.paddle2_y + self.paddle_speed, HEIGHT - self.paddle_h // 2)

        # Move ball
        self.ball_x += self.ball_vx
        self.ball_y += self.ball_vy

        # Bounce top/bottom
        if self.ball_y <= 0 or self.ball_y >= HEIGHT:
            self.ball_vy *= -1

        # Paddle 1 collision (left)
        if (self.ball_x <= 40 + self.paddle_w and
            abs(self.ball_y - self.paddle1_y) <= self.paddle_h // 2):
            self.ball_vx = abs(self.ball_vx)
            self.ball_x = 40 + self.paddle_w

        # Paddle 2 collision (right)
        elif (self.ball_x >= WIDTH - 40 - self.paddle_w and
              abs(self.ball_y - self.paddle2_y) <= self.paddle_h // 2):
            self.ball_vx = -abs(self.ball_vx)
            self.ball_x = WIDTH - 40 - self.paddle_w

        # Score
        if self.ball_x <= 0:
            self.score2 += 1
            self.get_logger().info(f'P2 scores! {self.score1}-{self.score2}')
            self.reset_ball()
        elif self.ball_x >= WIDTH:
            self.score1 += 1
            self.get_logger().info(f'P1 scores! {self.score1}-{self.score2}')
            self.reset_ball()

        # Win condition
        if self.score1 >= 5:
            self.game_status = 2
        elif self.score2 >= 5:
            self.game_status = 3

    def draw(self, screen, font, big_font):
        screen.fill(BLACK)

        # Center line
        for y in range(0, HEIGHT, 20):
            pygame.draw.rect(screen, (50, 50, 50), (WIDTH//2 - 2, y, 4, 10))

        # Paddles
        pygame.draw.rect(screen, GREEN,
            (40, self.paddle1_y - self.paddle_h//2, self.paddle_w, self.paddle_h))
        pygame.draw.rect(screen, RED,
            (WIDTH-40-self.paddle_w, self.paddle2_y - self.paddle_h//2,
             self.paddle_w, self.paddle_h))

        # Ball
        pygame.draw.circle(screen, WHITE,
            (int(self.ball_x), int(self.ball_y)), self.ball_size)

        # Score
        score_text = font.render(f'{self.score1}   {self.score2}', True, WHITE)
        screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, 20))

        # Player labels
        p1 = font.render('P1: W/S', True, GREEN)
        p2 = font.render('P2: ↑↓', True, RED)
        screen.blit(p1, (20, HEIGHT - 40))
        screen.blit(p2, (WIDTH - 100, HEIGHT - 40))

        # Game over
        if self.game_status == 2:
            txt = big_font.render('PLAYER 1 WINS! R to restart', True, YELLOW)
            screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - 30))
        elif self.game_status == 3:
            txt = big_font.render('PLAYER 2 WINS! R to restart', True, YELLOW)
            screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - 30))

        pygame.display.flip()

def main(args=None):
    rclpy.init(args=args)
    node = PongGame()

    # ROS spin in background thread
    ros_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    ros_thread.start()

    # Pygame setup
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('ROS 2 Pong Game')
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 60)
    big_font = pygame.font.Font(None, 40)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    node.score1 = 0
                    node.score2 = 0
                    node.game_status = 1
                    node.reset_ball()
                if event.key == pygame.K_ESCAPE:
                    running = False

        keys = pygame.key.get_pressed()
        node.update(keys)
        node.draw(screen, font, big_font)
        clock.tick(FPS)

    pygame.quit()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
